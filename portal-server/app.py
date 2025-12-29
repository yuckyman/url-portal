"""
Quart application for Wintermute Portal Router
Handles QR code portal requests and executes actions on the vault.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from quart import Quart, request, jsonify, redirect

from config import Config
from actions import ActionRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Quart(__name__)
app.config.from_object(Config)

# Initialize action registry
action_registry = ActionRegistry(Config.WINTERMUTE_REPO_PATH)
job_queue: asyncio.Queue["PortalJob"] = asyncio.Queue()
job_status: Dict[str, Dict[str, Any]] = {}
job_lock = asyncio.Lock()
portal_last_job: Dict[str, Dict[str, Any]] = {}
worker_tasks: list[asyncio.Task] = []


@dataclass
class PortalJob:
    """A queued portal job for background processing."""

    job_id: str
    portal_id: str
    action: str
    payload: Dict[str, Any]
    created_at: float = field(default_factory=time.time)


def utc_now_iso() -> str:
    """Return a UTC ISO-8601 timestamp."""
    return datetime.now(timezone.utc).isoformat()


def build_signature(portal_id: str, timestamp: int, secret: str) -> str:
    """Build the HMAC signature for a portal trigger."""
    message = f"{portal_id}:{timestamp}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_signature(portal_id: str, timestamp: Optional[int], signature: Optional[str]) -> Tuple[bool, str]:
    """Verify the HMAC signature when the webhook secret is configured."""
    secret = Config.PORTAL_WEBHOOK_SECRET
    if not secret:
        return True, ''
    if timestamp is None or not signature:
        return False, 'Missing signature or timestamp'
    now = int(time.time())
    if abs(now - timestamp) > Config.PORTAL_WEBHOOK_TTL_SECONDS:
        return False, 'Signature timestamp expired'
    expected = build_signature(portal_id, timestamp, secret)
    if not hmac.compare_digest(expected, signature):
        return False, 'Invalid signature'
    return True, ''


async def enqueue_job(
    portal_id: str,
    action: str,
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Enqueue a portal action and return job metadata."""
    now = time.time()
    async with job_lock:
        last_entry = portal_last_job.get(portal_id)
        if last_entry:
            last_time = last_entry["enqueued_at"]
            if now - last_time <= Config.PORTAL_DEDUP_WINDOW_SECONDS:
                return {
                    "job_id": last_entry["job_id"],
                    "status": "deduped",
                    "portal_id": portal_id,
                    "action": action,
                    "message": "Duplicate request ignored",
                }

        job_id = uuid.uuid4().hex
        job = PortalJob(
            job_id=job_id,
            portal_id=portal_id,
            action=action,
            payload=payload,
        )
        job_queue.put_nowait(job)
        status = {
            "job_id": job_id,
            "status": "queued",
            "portal_id": portal_id,
            "action": action,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
        job_status[job_id] = status
        portal_last_job[portal_id] = {
            "job_id": job_id,
            "enqueued_at": now,
        }

    return status


async def portal_worker(worker_id: int) -> None:
    """Background worker to process portal jobs."""
    while True:
        job = await job_queue.get()
        async with job_lock:
            job_status[job.job_id]["status"] = "in_progress"
            job_status[job.job_id]["updated_at"] = utc_now_iso()

        try:
            result = await action_registry.execute(job.action, job.payload)
            status = "succeeded" if result.get("success") else "failed"
            async with job_lock:
                job_status[job.job_id].update({
                    "status": status,
                    "result": result,
                    "updated_at": utc_now_iso(),
                })
            logger.info(
                "Job %s completed with status %s for portal %s",
                job.job_id,
                status,
                job.portal_id,
            )
        except Exception as e:
            logger.exception("Job %s failed: %s", job.job_id, e)
            async with job_lock:
                job_status[job.job_id].update({
                    "status": "failed",
                    "error": str(e),
                    "updated_at": utc_now_iso(),
                })
        finally:
            job_queue.task_done()


@app.before_serving
async def start_workers() -> None:
    """Start background worker tasks."""
    for index in range(Config.PORTAL_WORKERS):
        worker_tasks.append(asyncio.create_task(portal_worker(index)))


@app.after_serving
async def stop_workers() -> None:
    """Stop background worker tasks."""
    for task in worker_tasks:
        task.cancel()
    await asyncio.gather(*worker_tasks, return_exceptions=True)


def validate_portal_id(portal_id: str) -> bool:
    """
    Validate portal ID format: 2-24 chars, lowercase alphanumeric.
    
    Args:
        portal_id: The portal ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not portal_id:
        return False
    if len(portal_id) < 2 or len(portal_id) > 24:
        return False
    valid_chars = set('abcdefghijklmnopqrstuvwxyz0123456789')
    return all(c in valid_chars for c in portal_id.lower())


def load_portals_config() -> Dict[str, Any]:
    """
    Load portals.json from the wintermute repo.
    
    Returns:
        Dictionary of portal configurations
        
    Raises:
        FileNotFoundError: If portals.json doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    portals_path = Path(Config.WINTERMUTE_REPO_PATH) / '0_admin' / '00_index' / 'portals.json'
    
    if not portals_path.exists():
        logger.error(f"Portals config not found at {portals_path}")
        raise FileNotFoundError(f"Portals config not found: {portals_path}")
    
    with open(portals_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@app.route('/wm/p/<portal_id>', methods=['GET'])
async def portal_handler(portal_id: str):
    """
    Handle portal ID requests from QR codes.

    Returns a small HTML page that POSTs to the webhook endpoint.
    """
    try:
        # Validate portal ID format
        if not validate_portal_id(portal_id):
            logger.warning(f"Invalid portal ID format: {portal_id}")
            return jsonify({
                'error': 'Invalid portal ID format',
                'message': 'Portal ID must be 2-24 lowercase alphanumeric characters'
            }), 400
        
        # Load portals config
        portals = load_portals_config()
        
        if portal_id not in portals:
            logger.warning(f"Portal ID not found: {portal_id}")
            return jsonify({
                'error': 'Portal not found',
                'message': f'No configuration found for portal ID: {portal_id}'
            }), 404
        
        portal_config = portals[portal_id]
        action = portal_config.get('action')
        
        if not action:
            logger.error(f"Portal {portal_id} missing action")
            return jsonify({
                'error': 'Invalid portal configuration',
                'message': 'Portal configuration missing action'
            }), 500
        
        logger.info(f"Portal {portal_id} requested, action: {action}")
        
        portal_label = portal_config.get('label', action)
        signature_payload = {}
        if Config.PORTAL_WEBHOOK_SECRET:
            timestamp = int(time.time())
            signature_payload = {
                'timestamp': timestamp,
                'signature': build_signature(portal_id, timestamp, Config.PORTAL_WEBHOOK_SECRET),
            }

        payload_json = json.dumps({
            'portal_id': portal_id,
            **signature_payload,
        })

        html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Wintermute Portal</title>
    <style>
      body {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
        margin: 0;
        padding: 2rem 1.5rem;
        color: #e6e6e6;
        background: #0b0f14;
      }}
      .card {{
        max-width: 640px;
        margin: 0 auto;
        background: #101722;
        border-radius: 18px;
        padding: 24px;
        border: 1px solid #1b2636;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
      }}
      .title {{
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
      }}
      .subtitle {{
        color: #9aa7b5;
        margin-bottom: 1.5rem;
      }}
      .status {{
        background: #0b0f14;
        border: 1px solid #223247;
        padding: 12px;
        border-radius: 12px;
        font-size: 0.95rem;
      }}
      .status strong {{
        color: #5dd39e;
      }}
      .meta {{
        margin-top: 18px;
        font-size: 0.85rem;
        color: #7c8b99;
      }}
    </style>
  </head>
  <body>
    <div class="card">
      <div class="title">portal: {portal_id} → {portal_label}</div>
      <div class="subtitle">Triggering action in the background…</div>
      <div class="status" id="status">Sending webhook…</div>
      <div class="meta">You can close this page once accepted.</div>
    </div>
    <script>
      const statusEl = document.getElementById('status');
      const payload = {payload_json};

      const pollJob = (jobId) => {{
        const pollInterval = 1000;
        const poll = () => {{
          fetch(`/wm/jobs/${{jobId}}`)
            .then(async (resp) => {{
              const body = await resp.json().catch(() => ({{}}));
              if (!resp.ok) {{
                statusEl.textContent = `Error: ${{body.message || resp.statusText}}`;
                return;
              }}
              if (body.status === 'failed') {{
                statusEl.textContent = `Error: ${{body.error || 'Job failed'}}`;
                return;
              }}
              if (body.status === 'succeeded') {{
                const giteaUrl = body.result && body.result.gitea_url;
                if (giteaUrl) {{
                  statusEl.textContent = 'Opening note in Gitea...';
                  window.location.href = giteaUrl;
                  return;
                }}
                statusEl.textContent = 'Completed';
                return;
              }}
              statusEl.textContent = `Status: ${{body.status}}`;
              setTimeout(poll, pollInterval);
            }})
            .catch((err) => {{
              statusEl.textContent = `Error: ${{err.message}}`;
            }});
        }};
        poll();
      }};

      fetch('/wm/hooks/portal', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify(payload)
      }})
        .then(async (resp) => {{
          const body = await resp.json().catch(() => ({{}}));
          if (!resp.ok) {{
            statusEl.textContent = `Error: ${{body.message || resp.statusText}}`;
            return;
          }}
          statusEl.innerHTML = `<strong>Accepted</strong> · Job ${{body.job_id}}`;
          if (body.job_id) {{
            pollJob(body.job_id);
          }}
        }})
        .catch((err) => {{
          statusEl.textContent = `Error: ${{err.message}}`;
        }});
    </script>
  </body>
</html>
"""
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
        
    except FileNotFoundError as e:
        logger.error(f"Portals config not found: {e}")
        return jsonify({
            'error': 'Configuration error',
            'message': 'Portals configuration file not found'
        }), 500
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in portals config: {e}")
        return jsonify({
            'error': 'Configuration error',
            'message': 'Invalid portals configuration file'
        }), 500
    except Exception as e:
        logger.exception(f"Unexpected error in portal_handler: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/wm/hooks/portal', methods=['POST'])
async def portal_webhook():
    """
    Webhook endpoint that enqueues portal actions.

    Expected JSON body:
    {
        "portal_id": "dly",
        "timestamp": 1700000000,
        "signature": "hex..."
    }
    """
    try:
        data = await request.get_json()

        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must be JSON'
            }), 400

        portal_id = data.get('portal_id')
        if not portal_id:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Missing portal_id'
            }), 400

        if not validate_portal_id(portal_id):
            return jsonify({
                'error': 'Invalid portal ID format',
                'message': 'Portal ID must be 2-24 lowercase alphanumeric characters'
            }), 400

        timestamp = data.get('timestamp')
        signature = data.get('signature')
        try:
            timestamp_int = int(timestamp) if timestamp is not None else None
        except (TypeError, ValueError):
            return jsonify({
                'error': 'Invalid signature timestamp',
                'message': 'timestamp must be an integer'
            }), 400

        is_valid, error_message = verify_signature(portal_id, timestamp_int, signature)
        if not is_valid:
            return jsonify({
                'error': 'Unauthorized',
                'message': error_message
            }), 401

        portals = load_portals_config()
        portal_config = portals.get(portal_id)
        if not portal_config:
            return jsonify({
                'error': 'Portal not found',
                'message': f'No configuration found for portal ID: {portal_id}'
            }), 404

        action = portal_config.get('action')
        if not action:
            return jsonify({
                'error': 'Invalid portal configuration',
                'message': 'Portal configuration missing action'
            }), 500

        payload = {
            'portal_id': portal_id,
            'action': action,
            'config': portal_config,
        }
        job_info = await enqueue_job(portal_id, action, payload)
        job_info['accepted_at'] = utc_now_iso()
        return jsonify(job_info), 202

    except FileNotFoundError as e:
        logger.error(f"Portals config not found: {e}")
        return jsonify({
            'error': 'Configuration error',
            'message': 'Portals configuration file not found'
        }), 500
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in portals config: {e}")
        return jsonify({
            'error': 'Configuration error',
            'message': 'Invalid portals configuration file'
        }), 500
    except Exception as e:
        logger.exception(f"Unexpected error in portal_webhook: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/wm/jobs/<job_id>', methods=['GET'])
async def job_status_handler(job_id: str):
    """Fetch job status by job ID."""
    async with job_lock:
        status = job_status.get(job_id)
    if not status:
        return jsonify({
            'error': 'Job not found',
            'message': f'No job found with id {job_id}'
        }), 404
    return jsonify(status), 200


@app.route('/wm/act', methods=['POST'])
async def action_handler():
    """
    Execute portal actions.
    
    Expected JSON body:
    {
        "portal_id": "dly",
        "action": "view_daily",
        ...
    }
    """
    try:
        data = await request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must be JSON'
            }), 400
        
        portal_id = data.get('portal_id')
        action = data.get('action')
        
        if not portal_id or not action:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Missing portal_id or action'
            }), 400
        
        logger.info(f"Executing action: {action} for portal: {portal_id}")
        
        # Execute the action
        result = await action_registry.execute(action, data)
        
        if result.get('success'):
            gitea_url = result.get('gitea_url')
            wants_redirect = (
                request.args.get('redirect') == 'gitea'
                or request.accept_mimetypes.best == 'text/html'
            )
            if gitea_url and wants_redirect:
                return redirect(gitea_url)
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.exception(f"Unexpected error in action_handler: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e),
            'success': False
        }), 500


@app.route('/health', methods=['GET'])
async def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'wintermute-portal-router'
    }), 200


@app.route('/wm/endpoints', methods=['GET'])
async def list_endpoints():
    """List available endpoints and basic usage."""
    return jsonify({
        'endpoints': [
            {
                'method': 'GET',
                'path': '/wm/p/<portal_id>',
                'description': 'Lookup portal info and action for a portal ID.'
            },
            {
                'method': 'POST',
                'path': '/wm/act',
                'description': 'Execute a portal action (direct, synchronous).'
            },
            {
                'method': 'POST',
                'path': '/wm/hooks/portal',
                'description': 'Webhook endpoint to enqueue portal actions.'
            },
            {
                'method': 'GET',
                'path': '/wm/jobs/<job_id>',
                'description': 'Fetch webhook job status.'
            },
            {
                'method': 'GET',
                'path': '/wm/endpoints',
                'description': 'List available endpoints.'
            },
            {
                'method': 'GET',
                'path': '/health',
                'description': 'Health check.'
            }
        ]
    }), 200


if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
