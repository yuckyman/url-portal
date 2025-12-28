"""
Mac listener service for opening apps, URLs, and tmux presets.
"""

import hashlib
import hmac
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse, quote
import subprocess

from quart import Quart, jsonify, request

from config import Config


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Quart(__name__)
app.config.from_object(Config)


def _get_client_ip() -> str:
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or ''


def _allowlist_ok(ip: str) -> bool:
    if not Config.ALLOWED_IPS:
        return not Config.ALLOWLIST_REQUIRED
    return ip in Config.ALLOWED_IPS


def _signature_ok(body: bytes, timestamp: str, signature: str) -> bool:
    if not Config.SHARED_SECRET:
        return False
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False
    if abs(time.time() - ts) > Config.MAX_SKEW_SECONDS:
        return False
    message = f'{timestamp}.'.encode('utf-8') + body
    digest = hmac.new(
        Config.SHARED_SECRET.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(digest, signature)


async def _read_json_body() -> Tuple[Optional[Dict[str, Any]], bytes]:
    body = await request.get_data() or b''
    if not body:
        return None, body
    try:
        return json.loads(body.decode('utf-8')), body
    except json.JSONDecodeError:
        return None, body


def _error(message: str, status: int = 400):
    return jsonify({'success': False, 'message': message}), status


def _normalize_path(path_str: str) -> Optional[Path]:
    if not path_str:
        return None
    path = Path(path_str).expanduser().resolve()
    if not Config.ALLOWED_ROOTS:
        return path
    for root in Config.ALLOWED_ROOTS:
        try:
            path.relative_to(root)
            return path
        except ValueError:
            continue
    return None


def _valid_obsidian_file(file_path: str) -> bool:
    if not file_path:
        return False
    candidate = Path(file_path)
    if candidate.is_absolute():
        return False
    return '..' not in candidate.parts


def _open_app_with_path(app_name: str, path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, f'Path not found: {path}'
    try:
        subprocess.run(
            ['open', '-a', app_name, str(path)],
            check=True
        )
    except subprocess.CalledProcessError as exc:
        return False, f'Failed to open {app_name}: {exc}'
    return True, f'Opened {app_name}'


def _activate_app(app_name: str) -> None:
    subprocess.run(
        ['osascript', '-e', f'tell application "{app_name}" to activate'],
        check=False
    )


def _open_url(url: str, app_name: Optional[str]) -> Tuple[bool, str]:
    if not url:
        return False, 'Missing url'
    parsed = urlparse(url)
    if parsed.scheme not in Config.ALLOWED_URL_SCHEMES:
        return False, f'URL scheme not allowed: {parsed.scheme}'
    cmd = ['open']
    if app_name:
        if Config.ALLOWED_URL_APPS and app_name not in Config.ALLOWED_URL_APPS:
            return False, f'Browser app not allowed: {app_name}'
        cmd += ['-a', app_name]
    cmd.append(url)
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        return False, f'Failed to open url: {exc}'
    return True, 'Opened url'


def _open_obsidian_uri(vault: str, file_path: str) -> Tuple[bool, str, str]:
    if vault not in Config.OBSIDIAN_VAULTS:
        return False, f'Vault not allowed: {vault}', ''
    if not _valid_obsidian_file(file_path):
        return False, 'Invalid Obsidian file path', ''
    encoded_path = quote(file_path)
    uri = f'obsidian://open?vault={quote(vault)}&file={encoded_path}'
    try:
        subprocess.run(['open', uri], check=True)
    except subprocess.CalledProcessError as exc:
        return False, f'Failed to open obsidian uri: {exc}', uri
    _activate_app('Obsidian')
    return True, 'Opened Obsidian via URI', uri


def _load_presets() -> Dict[str, Dict[str, Any]]:
    presets_path = Config.PRESETS_PATH
    if not presets_path.is_absolute():
        presets_path = Path(__file__).parent / presets_path
    if not presets_path.exists():
        logger.error('Presets file not found: %s', presets_path)
        return {}
    try:
        with open(presets_path, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        logger.error('Invalid presets JSON: %s', exc)
        return {}
    return data


def _spawn_tmux_preset(name: str, cwd: Path) -> Tuple[bool, str]:
    presets = _load_presets()
    preset = presets.get(name)
    if not preset:
        return False, f'Unknown preset: {name}'
    command = preset.get('command')
    if not command:
        return False, f'Preset {name} missing command'

    session = preset.get('session', name)

    try:
        has_session = subprocess.run(
            ['tmux', 'has-session', '-t', session],
            check=False
        )
        if has_session.returncode != 0:
            subprocess.run(
                ['tmux', 'new-session', '-d', '-s', session, '-c', str(cwd), command],
                check=True
            )
    except subprocess.CalledProcessError as exc:
        return False, f'Failed to create tmux session: {exc}'

    _activate_app(Config.TERMINAL_APP)
    subprocess.run(
        [
            'osascript',
            '-e',
            f'tell application "{Config.TERMINAL_APP}" to do script "tmux attach -t {session}"'
        ],
        check=False
    )
    return True, f'Tmux session ready: {session}'


def _require_security(body: bytes) -> Optional[Tuple[Dict[str, Any], int]]:
    ip = _get_client_ip()
    if not _allowlist_ok(ip):
        return {'success': False, 'message': 'IP not allowed'}, 403

    if Config.SIGNATURE_REQUIRED:
        timestamp = request.headers.get('X-WM-Timestamp', '')
        signature = request.headers.get('X-WM-Signature', '')
        if not _signature_ok(body, timestamp, signature):
            return {'success': False, 'message': 'Invalid signature'}, 401
    return None


@app.before_request
async def enforce_security():
    if request.method == 'GET':
        return None
    _, body = await _read_json_body()
    security_error = _require_security(body)
    if security_error:
        payload, status = security_error
        return jsonify(payload), status
    return None


@app.route('/mac/open/obsidian', methods=['POST'])
async def open_obsidian():
    data, _ = await _read_json_body()
    if not data:
        return _error('Invalid JSON body')

    path_str = data.get('path')
    vault = data.get('vault')
    file_path = data.get('file')

    if vault and file_path:
        ok, message, uri = _open_obsidian_uri(vault, file_path)
        if ok:
            return jsonify({'success': True, 'message': message, 'uri': uri})
        return _error(message)

    if not path_str:
        return _error('Missing path or vault/file')

    path = _normalize_path(path_str)
    if not path:
        return _error('Path not allowed', 403)

    ok, message = _open_app_with_path('Obsidian', path)
    _activate_app('Obsidian')
    if ok:
        return jsonify({'success': True, 'message': message, 'path': str(path)})
    return _error(message)


@app.route('/mac/open/cursor', methods=['POST'])
async def open_cursor():
    data, _ = await _read_json_body()
    if not data:
        return _error('Invalid JSON body')

    path_str = data.get('path')
    if not path_str:
        return _error('Missing path')

    path = _normalize_path(path_str)
    if not path:
        return _error('Path not allowed', 403)

    ok, message = _open_app_with_path('Cursor', path)
    _activate_app('Cursor')
    if ok:
        return jsonify({'success': True, 'message': message, 'path': str(path)})
    return _error(message)


@app.route('/mac/open/url', methods=['POST'])
async def open_url():
    data, _ = await _read_json_body()
    if not data:
        return _error('Invalid JSON body')

    url = data.get('url')
    app_name = data.get('app')
    ok, message = _open_url(url, app_name)
    if ok:
        return jsonify({'success': True, 'message': message, 'url': url})
    return _error(message)


@app.route('/mac/spawn/agent', methods=['POST'])
async def spawn_agent():
    data, _ = await _read_json_body()
    if not data:
        return _error('Invalid JSON body')

    preset = data.get('preset')
    cwd_str = data.get('cwd')
    if not preset:
        return _error('Missing preset')
    if not cwd_str:
        return _error('Missing cwd')

    cwd = _normalize_path(cwd_str)
    if not cwd:
        return _error('cwd not allowed', 403)

    ok, message = _spawn_tmux_preset(preset, cwd)
    if ok:
        return jsonify({'success': True, 'message': message, 'preset': preset})
    return _error(message)


@app.route('/health', methods=['GET'])
async def health_check():
    return jsonify({'status': 'healthy', 'service': 'mac-listener'}), 200


if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
