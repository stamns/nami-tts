from flask import Flask, request, Response, jsonify, render_template_string, current_app
from flask_cors import CORS
from nano_tts import NanoAITTS
import threading
import time
import os
import logging
import gzip
import hashlib
from typing import Optional, Tuple, Dict, Any
from dotenv import load_dotenv


def _find_mp3_sync_offset(data: bytes, max_scan: int = 4096) -> Optional[int]:
    if not data or len(data) < 2:
        return None

    scan_len = min(len(data), max_scan)
    for i in range(scan_len - 1):
        if data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0:
            return i
    return None


def _parse_id3v2_tag_end(data: bytes) -> Optional[int]:
    if len(data) < 10 or not data.startswith(b"ID3"):
        return None

    size_bytes = data[6:10]
    if any(b & 0x80 for b in size_bytes):
        return None

    size = (size_bytes[0] << 21) | (size_bytes[1] << 14) | (size_bytes[2] << 7) | size_bytes[3]
    return 10 + size


def validate_and_normalize_mp3(audio_data: bytes) -> Tuple[bool, str, bytes, Dict[str, Any]]:
    debug: Dict[str, Any] = {
        "original_len": 0 if not audio_data else len(audio_data),
        "decompressed": False,
        "id3_present": False,
        "id3_declared_end": None,
        "first_sync_offset": None,
        "trimmed_offset": None,
        "normalized_len": 0,
        "first16_hex": "" if not audio_data else audio_data[:16].hex(),
        "sha256": "",
    }

    if not audio_data:
        return False, "音频数据为空", b"", debug

    if len(audio_data) >= 2 and audio_data[0] == 0x1F and audio_data[1] == 0x8B:
        try:
            audio_data = gzip.decompress(audio_data)
            debug["decompressed"] = True
            debug["first16_hex"] = audio_data[:16].hex()
        except Exception:
            pass

    if audio_data.startswith(b"ID3"):
        debug["id3_present"] = True
        id3_end = _parse_id3v2_tag_end(audio_data)
        debug["id3_declared_end"] = id3_end
        if id3_end is not None and id3_end + 1 < len(audio_data):
            if audio_data[id3_end] == 0xFF and (audio_data[id3_end + 1] & 0xE0) == 0xE0:
                debug["first_sync_offset"] = id3_end
                debug["normalized_len"] = len(audio_data)
                debug["sha256"] = hashlib.sha256(audio_data).hexdigest()
                return True, "有效的MP3文件(ID3标签)", audio_data, debug

    sync_offset = _find_mp3_sync_offset(audio_data)
    debug["first_sync_offset"] = sync_offset

    if sync_offset is None:
        debug["normalized_len"] = len(audio_data)
        debug["sha256"] = hashlib.sha256(audio_data).hexdigest()
        return False, "未检测到MP3同步帧", audio_data, debug

    if sync_offset > 0:
        audio_data = audio_data[sync_offset:]
        debug["trimmed_offset"] = sync_offset
        debug["first16_hex"] = audio_data[:16].hex()

    debug["normalized_len"] = len(audio_data)
    debug["sha256"] = hashlib.sha256(audio_data).hexdigest()
    return True, "有效的MP3文件(包含同步帧)", audio_data, debug


def validate_audio_data(audio_data: bytes) -> Tuple[bool, str]:
    is_valid, msg, _, _ = validate_and_normalize_mp3(audio_data)
    return is_valid, msg

# 加载环境变量
load_dotenv()
# --- 配置 ---
STATIC_API_KEY = os.getenv('TTS_API_KEY', 'sk-nanoai-your-secret-key')
CACHE_DURATION_SECONDS = int(os.getenv('CACHE_DURATION', 2 * 60 * 60))
PORT = int(os.getenv('PORT', 5001))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('nano-tts')
# --- 缓存管理器 ---
class ModelCache:
    def __init__(self, tts_engine):
        self._tts_engine = tts_engine
        self._cache = {}
        self._last_updated = 0
        self._lock = threading.Lock()
        self.logger = logging.getLogger('ModelCache')
    def get_models(self):
        with self._lock:
            current_time = time.time()
            if not self._cache or (current_time - self._last_updated > CACHE_DURATION_SECONDS):
                self.logger.info("缓存过期或为空，正在刷新模型列表...")
                try:
                    self._tts_engine.load_voices()
                    self._cache = {tag: info['name'] for tag, info in self._tts_engine.voices.items()}
                    self._last_updated = current_time
                    self.logger.info(f"模型列表刷新成功，共找到 {len(self._cache)} 个模型。")
                except Exception as e:
                    self.logger.error(f"刷新模型列表失败: {str(e)}", exc_info=True)
            return self._cache
# --- 初始化 ---
app = Flask(__name__)
CORS(
    app,
    expose_headers=[
        'Content-Type',
        'Content-Length',
        'Content-Disposition',
        'X-Audio-Size',
        'X-Audio-Validation',
        'X-Audio-FirstFrameOffset',
    ],
)
tts_engine = None
model_cache = None
try:
    logger.info("正在初始化 TTS 引擎...")
    tts_engine = NanoAITTS()
    logger.info("TTS 引擎初始化完毕。")
    model_cache = ModelCache(tts_engine)
except Exception as e:
    logger.critical(f"TTS 引擎初始化失败: {str(e)}", exc_info=True)
# --- 完整HTML模板（必须保留，否则页面空白）---
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>纳米AI TTS - OpenAI 兼容接口</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .container { background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 800px; width: 100%; overflow: hidden; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { font-size: 28px; margin-bottom: 10px; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .content { padding: 30px; }
        .section { margin-bottom: 25px; }
        .section-title { font-size: 16px; font-weight: 600; color: #333; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-size: 14px; color: #555; margin-bottom: 8px; font-weight: 500; }
        input[type="text"], input[type="password"], textarea, select { width: 100%; padding: 12px 15px; border: 2px solid #e0e0e0; border-radius: 10px; font-size: 14px; transition: all 0.3s; font-family: inherit; }
        .password-wrapper { position: relative; display: flex; align-items: center; }
        .password-wrapper input { padding-right: 45px; }
        .toggle-password { position: absolute; right: 12px; cursor: pointer; font-size: 20px; user-select: none; transition: opacity 0.2s; }
        .toggle-password:hover { opacity: 0.7; }
        input:focus, textarea:focus, select:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
        textarea { resize: vertical; min-height: 120px; }
        .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 14px 30px; border-radius: 10px; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.3s; width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4); }
        .btn:active { transform: translateY(0); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .btn-secondary { background: #6c757d; margin-top: 10px; }
        .status { padding: 12px 15px; border-radius: 10px; margin-bottom: 20px; display: none; align-items: center; gap: 10px; }
        .status.show { display: flex; }
        .status.info { background: #e3f2fd; color: #1976d2; border: 1px solid #90caf9; }
        .status.success { background: #e8f5e9; color: #388e3c; border: 1px solid #81c784; }
        .status.error { background: #ffebee; color: #c62828; border: 1px solid #e57373; }
        .models-list { max-height: 300px; overflow-y: auto; border: 2px solid #e0e0e0; border-radius: 10px; padding: 15px; }
        .model-item { padding: 10px; margin-bottom: 8px; background: #f8f9fa; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: all 0.2s; }
        .model-item:hover { background: #e9ecef; transform: translateX(5px); }
        .model-item.selected { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .model-id { font-weight: 600; font-size: 13px; }
        .model-name { font-size: 12px; opacity: 0.8; }
        .spinner { display: inline-block; width: 16px; height: 16px; border: 3px solid rgba(255,255,255,.3); border-radius: 50%; border-top-color: white; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .audio-player { margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 10px; display: none; }
        .audio-player.show { display: block; }
        audio { width: 100%; margin-top: 10px; }
        .char-count { text-align: right; font-size: 12px; color: #999; margin-top: 5px; }
        .api-info { background: #f8f9fa; padding: 15px; border-radius: 10px; font-size: 13px; line-height: 1.6; color: #555; }
        .api-info code { background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎙️ 纳米AI TTS</h1>
            <p>OpenAI 兼容接口 - 本地语音合成服务</p>
        </div>
        <div class="content">
            <div id="status" class="status"></div>
            <div class="section">
                <div class="section-title">⚙️ 服务配置</div>
                <div class="form-group">
                    <label>API 地址</label>
                    <input type="text" id="apiBase" value="" placeholder="">
                </div>
                <div class="form-group">
                    <label>API 密钥</label>
                    <div class="password-wrapper">
                        <input type="password" id="apiKey" value="sk-nanoai-your-secret-key" placeholder="sk-nanoai-your-secret-key">
                        <span class="toggle-password" onclick="togglePasswordVisibility()" id="toggleIcon">👁️</span>
                    </div>
                </div>
                <button class="btn btn-secondary" onclick="loadModels()">
                    <span id="loadModelsIcon">🔄</span>
                    <span>加载模型列表</span>
                </button>
            </div>
            <div class="section">
                <div class="section-title">🎵 选择声音模型</div>
                <div id="modelsList" class="models-list">
                    <div style="text-align: center; color: #999; padding: 20px;">
                        点击上方"加载模型列表"按钮获取可用声音
                    </div>
                </div>
            </div>
            <div class="section">
                <div class="section-title">📝 输入文本</div>
                <div class="form-group">
                    <textarea id="textInput" placeholder="请输入要转换为语音的文本..." oninput="updateCharCount()"></textarea>
                    <div class="char-count" id="charCount">字符数: 0</div>
                </div>
            </div>
            <button class="btn" id="generateBtn" onclick="generateSpeech()">
                <span>🎵</span>
                <span>生成语音</span>
            </button>
            <div id="audioPlayer" class="audio-player">
                <div class="section-title">🔊 生成的语音</div>
                <audio id="audio" controls preload="metadata"></audio>
                <button class="btn btn-secondary" onclick="downloadAudio()" style="margin-top: 10px;">
                    <span>💾</span>
                    <span>下载音频</span>
                </button>
            </div>
            <div class="section" style="margin-top: 30px;">
                <div class="section-title">ℹ️ API 使用说明</div>
                <div class="api-info">
                    <p><strong>接口地址：</strong> <code>POST /v1/audio/speech</code></p>
                    <p><strong>请求示例：</strong></p>
                    <pre style="background: #e9ecef; padding: 10px; border-radius: 5px; margin-top: 5px; overflow-x: auto;">curl http://127.0.0.1:5001/v1/audio/speech \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "DeepSeek", "input": "测试文本"}' \
  --output speech.mp3</pre>
                </div>
            </div>
        </div>
    </div>
    <script>
        let selectedModel = null;
        let currentAudioBlob = null;
        let currentAudioUrl = null;
        window.addEventListener('load', () => {
            const apiBaseInput = document.getElementById('apiBase');
            if (!apiBaseInput.value) apiBaseInput.value = window.location.origin;
            document.getElementById('toggleIcon').style.opacity = '0.6';
        });
        function updateCharCount() {
            const text = document.getElementById('textInput').value;
            const maxLength = 500;
            const currentLength = text.length;
            document.getElementById('charCount').textContent = `字符数: ${currentLength}/${maxLength}`;
            document.getElementById('generateBtn').disabled = currentLength > maxLength;
        }
        function togglePasswordVisibility() {
            const apiKeyInput = document.getElementById('apiKey');
            const toggleIcon = document.getElementById('toggleIcon');
            if (apiKeyInput.type === 'password') {
                apiKeyInput.type = 'text';
                toggleIcon.textContent = '🔓';
                toggleIcon.style.opacity = '1';
            } else {
                apiKeyInput.type = 'password';
                toggleIcon.textContent = '👁️';
                toggleIcon.style.opacity = '0.6';
            }
        }
        function showStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status ${type} show`;
            if (type === 'success' || type === 'error') setTimeout(() => status.classList.remove('show'), 5000);
        }
        async function loadModels() {
            const apiBase = document.getElementById('apiBase').value;
            const btn = event.target.closest('button');
            const icon = document.getElementById('loadModelsIcon');
            if (!apiBase) { showStatus('❌ 请先填写API地址', 'error'); return; }
            btn.disabled = true;
            icon.innerHTML = '<span class="spinner"></span>';
            showStatus('正在加载模型列表...', 'info');
            try {
                const response = await fetch(`${apiBase}/v1/models`);
                if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                const data = await response.json();
                const models = data.data || [];
                if (models.length === 0) throw new Error('未找到可用模型');
                renderModels(models);
                showStatus(`✓ 成功加载 ${models.length} 个模型`, 'success');
            } catch (error) {
                showStatus(`❌ 加载失败: ${error.message}`, 'error');
                console.error('加载模型失败:', error);
            } finally {
                btn.disabled = false;
                icon.textContent = '🔄';
            }
        }
        function renderModels(models) {
            const container = document.getElementById('modelsList');
            container.innerHTML = models.map(model => `
                <div class="model-item" onclick="selectModel('${model.id}')">
                    <div>
                        <div class="model-id">${model.id}</div>
                        <div class="model-name">${model.description || model.id}</div>
                    </div>
                    <div>🎤</div>
                </div>
            `).join('');
        }
        function selectModel(modelId) {
            selectedModel = modelId;
            document.querySelectorAll('.model-item').forEach(item => item.classList.remove('selected'));
            event.currentTarget.classList.add('selected');
            showStatus(`✓ 已选择模型: ${modelId}`, 'success');
        }
        function cleanupAudioUrl() {
            if (currentAudioUrl) {
                try { URL.revokeObjectURL(currentAudioUrl); } catch (e) { console.warn('清理音频URL失败:', e); }
                currentAudioUrl = null;
            }
        }
        async function generateSpeech() {
            const apiBase = document.getElementById('apiBase').value;
            const apiKey = document.getElementById('apiKey').value;
            const textInput = document.getElementById('textInput').value.trim();
            const btn = document.getElementById('generateBtn');
            if (!apiBase) { showStatus('❌ 请先填写API地址', 'error'); return; }
            if (!selectedModel) { showStatus('❌ 请先选择一个声音模型', 'error'); return; }
            if (!textInput) { showStatus('❌ 请输入要转换的文本', 'error'); return; }
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span><span>生成中...</span>';
            showStatus('正在生成语音...', 'info');
            cleanupAudioUrl();
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 30000);
                const response = await fetch(`${apiBase}/v1/audio/speech`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model: selectedModel, input: textInput }),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                if (!response.ok) {
                    let errorMsg = `HTTP ${response.status}`;
                    try { const errorData = await response.json(); errorMsg = errorData.error || errorMsg; } catch (e) {}
                    throw new Error(errorMsg);
                }
                const contentTypeHeader = response.headers.get('Content-Type') || '';
                const contentLengthHeader = response.headers.get('Content-Length') || '';
                const contentEncodingHeader = response.headers.get('Content-Encoding') || '';
                console.log('TTS响应头:', {
                    contentType: contentTypeHeader,
                    contentLength: contentLengthHeader,
                    contentEncoding: contentEncodingHeader,
                    audioValidation: response.headers.get('X-Audio-Validation') || '',
                    audioSize: response.headers.get('X-Audio-Size') || '',
                    audioFirstFrameOffset: response.headers.get('X-Audio-FirstFrameOffset') || ''
                });

                const audioArrayBuffer = await response.arrayBuffer();
                const audioU8 = new Uint8Array(audioArrayBuffer);
                const first16Hex = Array.from(audioU8.slice(0, 16))
                    .map(b => b.toString(16).padStart(2, '0'))
                    .join('');

                console.log(`音频ArrayBuffer: ${audioArrayBuffer.byteLength} bytes, first16=${first16Hex}`);

                if (contentLengthHeader) {
                    const expected = Number(contentLengthHeader);
                    if (!Number.isNaN(expected) && expected !== audioArrayBuffer.byteLength) {
                        console.warn('Content-Length与实际长度不一致:', expected, audioArrayBuffer.byteLength);
                    }
                }

                let blobType = contentTypeHeader.split(';')[0].trim();
                if (!blobType || !blobType.startsWith('audio/')) blobType = 'audio/mpeg';

                const audioBlob = new Blob([audioArrayBuffer], { type: blobType });
                if (!audioBlob.type.startsWith('audio/')) console.warn('警告: 返回的数据可能不是音频格式:', audioBlob.type);

                currentAudioBlob = audioBlob;
                currentAudioUrl = (window.URL || window.webkitURL).createObjectURL(audioBlob);
                const audioElement = document.getElementById('audio');
                audioElement.pause();
                audioElement.src = '';
                audioElement.load();
                audioElement.src = currentAudioUrl;
                audioElement.onloadedmetadata = () => {
                    console.log('音频metadata加载完成:', {
                        duration: audioElement.duration,
                        readyState: audioElement.readyState
                    });
                };

                audioElement.onerror = (e) => {
                    console.error('音频加载错误:', e, audioElement.error);
                    showStatus('❌ 音频播放失败，请尝试下载后播放', 'error');
                };

                audioElement.load();
                document.getElementById('audioPlayer').classList.add('show');
                showStatus('✓ 语音生成成功！', 'success');
                try { const playPromise = audioElement.play(); if (playPromise) playPromise.catch(e => console.warn('自动播放被阻止:', e)); } catch (e) { console.warn('播放失败:', e); }
            } catch (error) {
                const msg = error.name === 'AbortError' ? '❌ 请求超时，请缩短文本或检查网络' : `❌ 生成失败: ${error.message}`;
                showStatus(msg, 'error');
                console.error('生成语音失败:', error);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<span>🎵</span><span>生成语音</span>';
            }
        }
        function downloadAudio() {
            if (!currentAudioBlob) { showStatus('❌ 没有可下载的音频', 'error'); return; }
            try {
                const url = (window.URL || window.webkitURL).createObjectURL(currentAudioBlob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `nanoai_speech_${Date.now()}.mp3`;
                document.body.appendChild(a);
                a.click();
                setTimeout(() => { document.body.removeChild(a); (window.URL || window.webkitURL).revokeObjectURL(url); }, 100);
                showStatus('✓ 音频下载成功', 'success');
            } catch (error) {
                showStatus(`❌ 下载失败: ${error.message}`, 'error');
                console.error('下载失败:', error);
            }
        }
        window.addEventListener('beforeunload', cleanupAudioUrl);
    </script>
</body>
</html>"""
# --- 路由和API端点 ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)
@app.route('/v1/audio/speech', methods=['POST'])
def create_speech():
    if not tts_engine:
        logger.error("TTS引擎未初始化，无法处理语音合成请求")
        return jsonify({"error": "TTS engine is not available due to initialization failure."}), 503
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.warning("缺少或无效的Authorization头")
        return jsonify({"error": "Authorization header is missing or invalid"}), 401
    provided_key = auth_header.split(' ')[1]
    if provided_key != STATIC_API_KEY:
        logger.warning(f"无效API密钥: {provided_key[:5]}***")
        return jsonify({"error": "Invalid API Key"}), 401
    try:
        data = request.get_json()
    except Exception as e:
        logger.error(f"解析JSON失败: {str(e)}", exc_info=True)
        return jsonify({"error": "Invalid JSON body"}), 400
    model_id = data.get('model')
    text_input = data.get('input')
    if not model_id or not text_input:
        logger.warning("缺少必填字段: 'model'或'input'")
        return jsonify({"error": "Missing required fields: 'model' and 'input'"}), 400
    available_models = model_cache.get_models()
    if model_id not in available_models:
        logger.warning(f"模型不存在: {model_id}")
        return jsonify({"error": f"Model '{model_id}' not found. Use /v1/models to see available models."}), 404
    logger.info(f"语音合成请求: model='{model_id}', input='{text_input[:30]}...'")
    try:
        audio_data = tts_engine.get_audio(text_input, voice=model_id)
    except Exception as e:
        current_app.logger.error(f"TTS引擎错误: {str(e)}", exc_info=True)
        return jsonify({"error": "TTS engine error", "details": str(e)}), 500
    is_valid, validation_msg, normalized_audio, debug = validate_and_normalize_mp3(audio_data)
    if not is_valid:
        current_app.logger.error(
            f"音频无效: {validation_msg}; len={debug.get('original_len')}; first16={debug.get('first16_hex')}"
        )
        return (
            jsonify(
                {
                    "error": "Invalid audio data",
                    "details": validation_msg,
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

    current_app.logger.info(
        "音频验证成功: %s; len=%s; first16=%s; first_sync_offset=%s; trimmed_offset=%s; decompressed=%s",
        validation_msg,
        len(audio_data),
        debug.get('first16_hex'),
        debug.get('first_sync_offset'),
        debug.get('trimmed_offset'),
        debug.get('decompressed'),
    )

    resp = Response(audio_data, mimetype='audio/mpeg')
    resp.headers['Content-Disposition'] = 'inline; filename="speech.mp3"'
    resp.headers['Content-Length'] = str(len(audio_data))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    resp.headers['Accept-Ranges'] = 'bytes'

    resp.headers['X-Audio-Size'] = str(len(audio_data))
    resp.headers['X-Audio-Validation'] = validation_msg
    resp.headers['X-Audio-FirstFrameOffset'] = str(
        debug.get('trimmed_offset') or debug.get('first_sync_offset') or 0
    )
    resp.headers.pop('Content-Encoding', None)

    current_app.logger.info(
        "返回音频响应头: Content-Type=%s Content-Length=%s Cache-Control=%s",
        resp.headers.get('Content-Type'),
        resp.headers.get('Content-Length'),
        resp.headers.get('Cache-Control'),
    )

    return resp


@app.route('/v1/audio/diagnose', methods=['POST'])
def diagnose_audio():
    if not tts_engine:
        return jsonify({"error": "TTS engine is not available due to initialization failure."}), 503

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization header is missing or invalid"}), 401

    provided_key = auth_header.split(' ')[1]
    if provided_key != STATIC_API_KEY:
        return jsonify({"error": "Invalid API Key"}), 401

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    model_id = data.get('model')
    text_input = data.get('input')
    if not model_id or not text_input:
        return jsonify({"error": "Missing required fields: 'model' and 'input'"}), 400

    available_models = model_cache.get_models()
    if model_id not in available_models:
        return jsonify({"error": f"Model '{model_id}' not found. Use /v1/models to see available models."}), 404

    try:
        audio_data = tts_engine.get_audio(text_input, voice=model_id)
    except Exception as e:
        return jsonify({"error": "TTS engine error", "details": str(e)}), 500

    is_valid, validation_msg, normalized_audio, debug = validate_and_normalize_mp3(audio_data)

    return jsonify(
        {
            "ok": is_valid,
            "message": validation_msg,
            "request": {
                "model": model_id,
                "text_len": len(text_input),
            },
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


@app.route('/v1/models', methods=['GET'])
def list_models():
    if not model_cache:
        logger.error("模型缓存未初始化")
        return jsonify({"error": "TTS engine not initialized"}), 503
    available_models = model_cache.get_models()
    models_data = [{"id": k, "object": "model", "created": int(model_cache._last_updated), "owned_by": "nanoai", "description": v} for k, v in available_models.items()]
    return jsonify({"object": "list", "data": models_data})
@app.route('/health', methods=['GET'])
def health_check():
    if tts_engine and model_cache:
        model_count = len(model_cache.get_models())
        return jsonify({"status": "ok", "models_in_cache": model_count, "timestamp": int(time.time())}), 200
    return jsonify({"status": "error", "message": "TTS engine not initialized"}), 503
if __name__ == '__main__':
    if tts_engine:
        logger.info("预热模型缓存...")
        model_cache.get_models()
        logger.info(f"服务启动，端口 {PORT}")
        app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
    else:
        logger.critical("TTS引擎初始化失败，无法启动服务")
