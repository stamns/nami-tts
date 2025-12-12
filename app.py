from flask import Flask, request, Response, jsonify, render_template_string, current_app  # 修复：新增 current_app 导入
from flask_cors import CORS
from nano_tts import NanoAITTS
import threading
import time
import os
import logging
from dotenv import load_dotenv
def validate_audio_data(audio_data):
    """验证音频数据是否为有效的MP3格式（修复缩进错误）"""
    if not audio_data or len(audio_data) < 50:
        return False, "音频数据为空或过短"
    # 检查MP3文件头（修复缩进：以下代码需缩进4个空格）
    if audio_data.startswith(b'ID3'):  # ID3标签头（MP3标准格式）
        return True, "有效的MP3文件(ID3标签)"  # ✅ 缩进4个空格
    elif audio_data.startswith(b'\xff\xe3') or audio_data.startswith(b'\xff\xfb'):  # MP3音频帧头
        return True, "有效的MP3文件(音频帧头)"  # ✅ 缩进4个空格
    else:
        # 检查是否包含MP3同步帧（如未检测到文件头，但包含音频数据）
        if b'\xff' in audio_data[:100]:  # MP3同步帧特征
            return True, "可能有效的MP3文件(包含同步帧)"  # ✅ 缩进4个空格
        else:
            return False, "无效的MP3文件头（缺少关键标识）"  # ✅ 缩进4个空格
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
CORS(app)
tts_engine = None
model_cache = None
try:
    logger.info("正在初始化 TTS 引擎...")
    tts_engine = NanoAITTS()
    logger.info("TTS 引擎初始化完毕。")
    model_cache = ModelCache(tts_engine)
except Exception as e:
    logger.critical(f"TTS 引擎初始化失败: {str(e)}", exc_info=True)
# HTML模板（保持不变，此处省略以节省空间，实际使用时保留原模板）
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>纳米AI TTS - OpenAI 兼容接口</title>
    <style>
        /* 原CSS样式保持不变 */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        /* ... 其余CSS样式 ... */
    </style>
</head>
<body>
    <!-- 原HTML内容保持不变 -->
    <div class="container">
        <!-- ... 原HTML结构 ... -->
    </div>
    <script>
        // 原JavaScript代码保持不变
    </script>
</body>
</html>"""
# --- 路由和API端点 ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)
@app.route('/v1/audio/speech', methods=['POST'])    # 修复：规范路由格式（去除多余换行）
def create_speech():
    if not tts_engine:
        logger.error("TTS引擎未初始化，无法处理语音合成请求")
        return jsonify({"error": "TTS engine is not available due to initialization failure."}), 503
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.warning("接收到缺少或无效Authorization头的请求")
        return jsonify({"error": "Authorization header is missing or invalid"}), 401
    
    provided_key = auth_header.split(' ')[1]
    if provided_key != STATIC_API_KEY:
        logger.warning(f"接收到无效API密钥的请求，密钥: {provided_key[:5]}***")
        return jsonify({"error": "Invalid API Key"}), 401
    try:
        data = request.get_json()
    except Exception as e:
        logger.error(f"解析请求JSON失败: {str(e)}", exc_info=True)
        return jsonify({"error": "Invalid JSON body"}), 400
    model_id = data.get('model')
    text_input = data.get('input')
    if not model_id or not text_input:
        logger.warning("请求缺少必填字段: 'model'或'input'")
        return jsonify({"error": "Missing required fields: 'model' and 'input'"}), 400
    available_models = model_cache.get_models()
    if model_id not in available_models:
        logger.warning(f"请求了不存在的模型: {model_id}")
        return jsonify({"error": f"Model '{model_id}' not found. Please use the /v1/models endpoint to see available models."}), 404
    logger.info(f"收到语音合成请求: model='{model_id}', input='{text_input[:30]}...'")
    
    # 获取音频数据（带异常处理）
    try:
        audio_data = tts_engine.get_audio(text_input, voice=model_id)
    except Exception as e:
        current_app.logger.error(f"调用TTS引擎失败：{str(e)}", exc_info=True)
        return jsonify({"error": "TTS引擎错误", "details": str(e)}), 500
    
    # 验证音频数据（正常流程）
    is_valid, validation_msg = validate_audio_data(audio_data)
    if not is_valid:
        current_app.logger.error(f"音频生成失败：{validation_msg}")
        return jsonify({"error": "音频数据无效", "details": validation_msg}), 500
    
    current_app.logger.info(f"音频验证成功：{validation_msg}")
    logger.info(f"语音合成成功，模型: {model_id}, 文本长度: {len(text_input)}")
    
    # 返回音频响应
    return Response(
        audio_data,
        mimetype='audio/mpeg',
        headers={
            'Content-Disposition': 'inline; filename="speech.mp3"',
            'Content-Length': str(len(audio_data))
        }
    )
@app.route('/v1/models', methods=['GET'])    # 修复：规范路由格式
def list_models():
    if not model_cache:
        logger.error("模型缓存未初始化，无法列出模型")
        return jsonify({"error": "TTS engine is not available due to initialization failure."}), 503
    available_models = model_cache.get_models()
    logger.info(f"列出可用模型，共 {len(available_models)} 个")
    
    models_data = [
        {
            "id": model_id,
            "object": "model",
            "created": int(model_cache._last_updated),
            "owned_by": "nanoai",
            "description": model_name
        }
        for model_id, model_name in available_models.items()
    ]
    return jsonify({"object": "list", "data": models_data})
@app.route('/health', methods=['GET'])    # 修复：规范路由格式
def health_check():
    if tts_engine and model_cache:
        model_count = len(model_cache.get_models())
        logger.info(f"健康检查: 服务正常，模型数量: {model_count}")
        return jsonify({
            "status": "ok", 
            "models_in_cache": model_count,
            "timestamp": int(time.time())
        }), 200
    else:
        logger.error("健康检查失败: TTS引擎未初始化")
        return jsonify({"status": "error", "message": "TTS engine not initialized"}), 503
# --- 启动服务 ---
if __name__ == '__main__':
    if tts_engine:
        logger.info("正在预热模型缓存...")
        model_cache.get_models()
        logger.info(f"服务准备就绪，监听端口 {PORT}")
        app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
    else:
        logger.critical("无法启动Flask服务，因为TTS引擎初始化失败")
