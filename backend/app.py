from __future__ import annotations

import os
import time
import json
import base64
import hmac
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from flask import Flask, Response, current_app, jsonify, request, send_from_directory
from flask_cors import CORS

from backend.config import build_tts_manager
from backend.utils.audio import validate_and_normalize_mp3
from backend.utils.logger import setup_logging


load_dotenv()
logger = setup_logging("nami-tts")


PORT = int(os.getenv("PORT") or 5001)
DEBUG = (os.getenv("DEBUG") or "False").lower() == "true"

SERVICE_API_KEY = os.getenv("SERVICE_API_KEY") or os.getenv("TTS_API_KEY") or "sk-nanoai-your-secret-key"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
UI_CONFIG_FILE = PROJECT_ROOT / ".ui_config.json"
UI_CONFIG_SECRET = os.getenv("UI_CONFIG_SECRET") or SERVICE_API_KEY


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    if not key:
        raise ValueError("encryption key is empty")
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _ui_config_key_bytes() -> bytes:
    return hashlib.sha256(UI_CONFIG_SECRET.encode("utf-8")).digest()


def encrypt_ui_config(config: Dict[str, Any]) -> Dict[str, Any]:
    key = _ui_config_key_bytes()
    plaintext = json.dumps(config, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    mac = hmac.new(key, plaintext, hashlib.sha256).hexdigest()
    cipher = _xor_bytes(plaintext, key)
    return {
        "v": 1,
        "alg": "xor+sha256-hmac",
        "mac": mac,
        "data": base64.urlsafe_b64encode(cipher).decode("ascii"),
    }


def decrypt_ui_config(encrypted: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(encrypted, dict) or encrypted.get("v") != 1:
        raise ValueError("unsupported config format")

    key = _ui_config_key_bytes()
    cipher_b64 = encrypted.get("data")
    if not isinstance(cipher_b64, str) or not cipher_b64:
        raise ValueError("missing encrypted data")

    cipher = base64.urlsafe_b64decode(cipher_b64.encode("ascii"))
    plaintext = _xor_bytes(cipher, key)
    expected_mac = hmac.new(key, plaintext, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_mac, str(encrypted.get("mac") or "")):
        raise ValueError("invalid config mac")

    decoded = json.loads(plaintext.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("invalid config content")
    return decoded


def load_ui_config_from_disk() -> Optional[Dict[str, Any]]:
    try:
        if not UI_CONFIG_FILE.exists():
            return None
        with open(UI_CONFIG_FILE, "r", encoding="utf-8") as f:
            encrypted = json.load(f)
        return decrypt_ui_config(encrypted)
    except Exception as e:
        logger.warning("读取UI配置失败: %s", str(e))
        return None


def save_ui_config_to_disk(config: Dict[str, Any]) -> None:
    encrypted = encrypt_ui_config(config)
    with open(UI_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(encrypted, f, ensure_ascii=False, indent=2)


_tts_manager = build_tts_manager()


def _get_tts_manager():
    return _tts_manager


def _rebuild_tts_manager() -> None:
    global _tts_manager
    _tts_manager = build_tts_manager()


def _require_auth() -> Optional[Any]:
    auth_header = request.headers.get("Authorization") or ""
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authorization header is missing or invalid"}), 401

    provided_key = auth_header.split(" ", 1)[1]
    if provided_key != SERVICE_API_KEY:
        return jsonify({"error": "Invalid API Key"}), 401

    return None


FRONTEND_DIR = PROJECT_ROOT / "frontend"


app = Flask(__name__)
CORS(
    app,
    expose_headers=[
        "Content-Type",
        "Content-Length",
        "Content-Disposition",
        "X-Audio-Size",
        "X-Audio-Validation",
        "X-Audio-FirstFrameOffset",
        "X-TTS-Provider",
    ],
)


@app.route("/")
def index():
    if FRONTEND_DIR.joinpath("index.html").exists():
        return send_from_directory(FRONTEND_DIR, "index.html")
    return Response("frontend/index.html not found", status=404, mimetype="text/plain")


@app.route("/v1/providers", methods=["GET"])
def list_providers():
    manager = _get_tts_manager()

    providers = []
    for name, provider in manager.providers.items():
        health = provider.health_check()
        providers.append(
            {
                "name": name,
                "is_default": name == manager.default_provider,
                "priority": manager.priority_order.index(name) if name in manager.priority_order else None,
                "health": {
                    "ok": health.ok,
                    "message": health.message,
                    "details": health.details,
                },
            }
        )

    providers.sort(key=lambda x: (x["priority"] is None, x["priority"] or 9999, x["name"]))
    return jsonify({"object": "list", "data": providers})


@app.route("/v1/models", methods=["GET"])
def list_models():
    manager = _get_tts_manager()

    provider_name = request.args.get("provider")
    force_refresh = (request.args.get("force_refresh") or "false").lower() in ("true", "1", "yes")

    actual_provider, models = manager.get_models(provider_name, force_refresh=force_refresh)
    models_data = [
        {
            "id": model_id,
            "object": "model",
            "created": int(time.time()),
            "owned_by": actual_provider,
            "description": desc,
        }
        for model_id, desc in models.items()
    ]

    return jsonify({"object": "list", "provider": actual_provider, "data": models_data})


@app.route("/v1/audio/speech", methods=["POST"])
def create_speech():
    auth_resp = _require_auth()
    if auth_resp:
        return auth_resp

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    model_id = data.get("model")
    text_input = data.get("input")
    provider_name = data.get("provider")

    if not model_id or not text_input:
        return jsonify({"error": "Missing required fields: 'model' and 'input'"}), 400

    options: Dict[str, Any] = {
        "timeout": data.get("timeout"),
        "retry_count": data.get("retry_count"),
        "speed": data.get("speed"),
        "pitch": data.get("pitch"),
        "language": data.get("language"),
        "gender": data.get("gender"),
        "format": data.get("format"),
    }

    manager = _get_tts_manager()

    request_received_at = time.time()
    logger.info(
        "speech request: provider=%s model=%s text_len=%s local_epoch=%.3f",
        provider_name,
        model_id,
        len(text_input),
        request_received_at,
    )

    try:
        used_provider, audio_data, errors = manager.generate_with_fallback(
            text_input,
            model_id,
            provider_name=provider_name,
            **options,
        )
    except Exception as e:
        current_app.logger.error("TTS generate failed: %s", str(e), exc_info=True)
        return (
            jsonify(
                {
                    "error": "TTS generation failed",
                    "details": str(e),
                }
            ),
            500,
        )

    is_valid, validation_msg, normalized_audio, debug = validate_and_normalize_mp3(audio_data)
    if not is_valid:
        current_app.logger.error(
            "audio invalid: %s; len=%s; first16=%s",
            validation_msg,
            debug.get("original_len"),
            debug.get("first16_hex"),
        )
        return (
            jsonify(
                {
                    "error": "Invalid audio data",
                    "details": validation_msg,
                    "provider": used_provider,
                    "debug": {
                        "len": debug.get("original_len"),
                        "first16_hex": debug.get("first16_hex"),
                        "sha256": debug.get("sha256"),
                    },
                }
            ),
            500,
        )

    audio_data = normalized_audio

    resp = Response(audio_data, mimetype="audio/mpeg")
    resp.headers["Content-Disposition"] = 'inline; filename="speech.mp3"'
    resp.headers["Content-Length"] = str(len(audio_data))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    resp.headers["Accept-Ranges"] = "bytes"

    resp.headers["X-Audio-Size"] = str(len(audio_data))
    resp.headers["X-Audio-Validation"] = "valid"
    resp.headers["X-Audio-FirstFrameOffset"] = str(debug.get("trimmed_offset") or debug.get("first_sync_offset") or 0)
    resp.headers["X-TTS-Provider"] = used_provider

    # ensure no accidental content-encoding
    resp.headers.pop("Content-Encoding", None)

    if errors:
        current_app.logger.info(
            "fallback attempts: %s",
            [e.__dict__ for e in errors],
        )

    return resp


@app.route("/v1/audio/diagnose", methods=["GET", "POST"])
def diagnose():
    manager = _get_tts_manager()

    if request.method == "GET":
        providers = []
        for name, provider in manager.providers.items():
            health = provider.health_check()
            providers.append({"name": name, "ok": health.ok, "message": health.message, "details": health.details})

        nanoai = manager.providers.get("nanoai")
        time_status = None
        last_request_time_info = None
        if nanoai and hasattr(nanoai, "engine"):
            try:
                time_status = nanoai.engine.get_time_sync_status()
                last_request_time_info = nanoai.engine.get_last_request_time_info()
            except Exception:
                pass

        return jsonify(
            {
                "timestamp": int(time.time()),
                "service": {
                    "debug": DEBUG,
                    "providers": providers,
                },
                "time": {
                    "local_epoch_seconds": time.time(),
                    "upstream_time_sync": time_status,
                    "last_upstream_request": last_request_time_info,
                },
            }
        )

    auth_resp = _require_auth()
    if auth_resp:
        return auth_resp

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    model_id = data.get("model")
    text_input = data.get("input")
    provider_name = data.get("provider")
    if not model_id or not text_input:
        return jsonify({"error": "Missing required fields: 'model' and 'input'"}), 400

    used_provider, audio_data, errors = manager.generate_with_fallback(text_input, model_id, provider_name=provider_name)
    is_valid, validation_msg, normalized_audio, debug = validate_and_normalize_mp3(audio_data)

    return jsonify(
        {
            "ok": is_valid,
            "message": validation_msg,
            "provider": used_provider,
            "attempts": [e.__dict__ for e in errors],
            "request": {"model": model_id, "text_len": len(text_input)},
            "audio": {
                "len": len(audio_data) if audio_data else 0,
                "normalized_len": len(normalized_audio) if normalized_audio else 0,
                "first16_hex": debug.get("first16_hex"),
                "first_sync_offset": debug.get("first_sync_offset"),
                "trimmed_offset": debug.get("trimmed_offset"),
                "id3_present": debug.get("id3_present"),
                "id3_declared_end": debug.get("id3_declared_end"),
                "decompressed": debug.get("decompressed"),
                "sha256": debug.get("sha256"),
            },
        }
    )


@app.route("/v1/config", methods=["GET", "POST"])
def config_endpoint():
    global SERVICE_API_KEY

    manager = _get_tts_manager()

    if request.method == "GET":
        providers: Dict[str, Any] = {}
        for name, provider in manager.providers.items():
            health = provider.health_check()
            providers[name] = {
                "health_ok": health.ok,
                "health_message": health.message,
            }

        return jsonify(
            {
                "service_api_key_configured": bool(SERVICE_API_KEY and SERVICE_API_KEY != "sk-nanoai-your-secret-key"),
                "default_provider": manager.default_provider,
                "provider_priority": manager.priority_order,
                "providers": providers,
            }
        )

    auth_resp = _require_auth()
    if auth_resp:
        return auth_resp

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    allowlist = {
        "SERVICE_API_KEY",
        "TTS_API_KEY",
        "DEFAULT_TTS_PROVIDER",
        "TTS_PROVIDER_PRIORITY",
        "GOOGLE_API_KEY",
        "AZURE_API_KEY",
        "AZURE_REGION",
        "AZURE_ENDPOINT",
        "BAIDU_API_KEY",
        "BAIDU_SECRET_KEY",
        "ALIYUN_ACCESS_KEY_ID",
        "ALIYUN_ACCESS_KEY_SECRET",
    }

    updated = []
    for k, v in data.items():
        if k not in allowlist:
            continue
        if v is None:
            continue
        if not isinstance(v, str):
            v = str(v)
        os.environ[k] = v
        updated.append(k)

    SERVICE_API_KEY = os.getenv("SERVICE_API_KEY") or os.getenv("TTS_API_KEY") or SERVICE_API_KEY
    _rebuild_tts_manager()

    return jsonify({"ok": True, "updated": updated})


@app.route("/v1/ui/config", methods=["GET"])
def ui_config_public():
    """Public UI configuration endpoint"""
    stored = UI_CONFIG_FILE.exists()

    manager = _get_tts_manager()
    provider_info = {}
    for name, provider in manager.providers.items():
        health = provider.health_check()
        provider_info[name] = {
            "name": name.capitalize(),
            "available": health.ok,
        }

    return jsonify(
        {
            "server": {
                "defaultBaseUrl": request.host_url.rstrip("/"),
                "hasStoredConfig": stored,
            },
            "defaults": {
                "provider": manager.default_provider,
                "language": "auto",
                "speed": 1.0,
                "pitch": 1.0,
                "volume": 1.0,
                "format": "mp3",
            },
            "providers": provider_info,
        }
    )


@app.route("/v1/ui/config/secure", methods=["GET", "PUT"])
def ui_config_secure():
    """Secure UI configuration endpoint (requires auth)"""
    auth_resp = _require_auth()
    if auth_resp:
        return auth_resp

    if request.method == "GET":
        config = load_ui_config_from_disk() or {}
        return jsonify({"config": config})

    try:
        payload = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    config = payload.get("config")
    if not isinstance(config, dict):
        return jsonify({"error": "Missing or invalid field: config"}), 400

    try:
        save_ui_config_to_disk(config)
    except Exception as e:
        logger.error("保存UI配置失败: %s", str(e), exc_info=True)
        return jsonify({"error": "Failed to save config", "details": str(e)}), 500

    return jsonify({"ok": True})


@app.route("/health", methods=["GET"])
def health_check():
    manager = _get_tts_manager()

    provider_health: Dict[str, Any] = {}
    any_ok = False
    for name, provider in manager.providers.items():
        health = provider.health_check()
        provider_health[name] = {"ok": health.ok, "message": health.message}
        any_ok = any_ok or health.ok

    status_code = 200 if any_ok else 503

    return (
        jsonify(
            {
                "status": "ok" if any_ok else "error",
                "timestamp": int(time.time()),
                "providers": provider_health,
                "default_provider": manager.default_provider,
            }
        ),
        status_code,
    )


def main() -> None:
    logger.info("starting nami-tts on port %s", PORT)
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
