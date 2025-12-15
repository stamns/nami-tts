# nami-tts 本地部署可行性分析报告

## 1. 结论
**结论：YES（可以完整本地部署）**

nami-tts 项目具备良好的本地部署能力。项目架构简洁，后端基于 Flask，前端为单页 HTML 应用，无复杂的构建依赖。核心 TTS 功能虽然依赖外部 API（如 NanoAI、Google、Azure 等），但控制服务（API 网关和前端界面）可以完全在本地运行。

## 2. 详细分析

### 2.1 后端 (Flask)
- **依赖**：主要依赖为 `Flask`, `requests`, `gTTS`。`pydub` 为可选依赖（但在 `requirements.txt` 中未明确列出，但在代码中有引用），用于音频合并。
- **Vercel 耦合**：
  - 项目包含 Vercel 特定的配置文件 (`vercel.json`) 和入口 (`backend/api/index.py`)。
  - 代码中包含针对 Serverless 环境的时间漂移修复逻辑 (`time_sync`)，这在本地环境中是兼容的，甚至有助于解决本地时间不准的问题。
  - 缓存目录默认指向 `/tmp/cache`（Serverless 友好），但可通过环境变量 `CACHE_DIR` 修改，适应本地环境。
- **外部服务**：
  - 项目本质上是一个 TTS 聚合网关，实际的语音合成工作由云端提供商完成（NanoAI, Google, Azure 等）。
  - 本地部署**必须**能够访问互联网以连接这些上游服务。

### 2.2 前端 (React/HTML)
- **结构**：前端实现为一个独立的 `frontend/index.html` 文件，包含内嵌的 CSS 和 JavaScript。
- **构建**：**无需构建步骤**。没有 `package.json`，不需要 Node.js 环境。
- **API 调用**：前端代码通过相对路径或自动检测 `window.location.origin` 来调用后端 API，天然支持本地部署。

### 2.3 文件系统与路径
- **缓存**：默认使用 `/tmp/cache`。在 Windows 等系统上可能需要通过环境变量调整为合适的临时目录。
- **静态资源**：Flask 应用配置了从 `frontend` 目录直接服务 `index.html`，无需额外的 Web 服务器（如 Nginx）即可运行。

## 3. 依赖清单

### 系统依赖
- **Python**: 3.9+ (建议)
- **FFmpeg**: (强烈建议) 用于 `pydub` 进行音频处理和格式转换。若未安装，多段音频合并功能将降级为简单拼接。
- **网络**: 必须能访问互联网（连接 `bot.n.cn`, `googleapis.com` 等）。

### Python 依赖 (requirements.txt)
```text
Flask==2.3.3
Flask-CORS==4.0.0
gunicorn==21.2.0
python-dotenv==1.0.0
gTTS==2.5.4
requests==2.31.0
```
*建议添加 `pydub` 到依赖中以启用高级音频处理功能。*

## 4. 本地部署完整步骤

### 步骤 1: 环境准备
确保系统已安装 Python 3 和 FFmpeg。
```bash
# 检查 Python
python3 --version

# 检查 FFmpeg
ffmpeg -version
```

### 步骤 2: 获取代码与虚拟环境
```bash
git clone <repository_url>
cd nami-tts

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 步骤 3: 安装依赖
```bash
pip install -r requirements.txt
pip install pydub  # 建议安装
```

### 步骤 4: 配置环境变量
复制示例配置文件并修改：
```bash
cp .env.example .env
```
编辑 `.env` 文件：
- 设置 `SERVICE_API_KEY`: 设置一个安全的 API 密钥。
- 设置 `CACHE_DIR`: 本地开发可设置为 `./cache` 或保持默认。
- 配置其他 Provider 的 Key (如 Azure, Aliyun 等，如果需要)。

### 步骤 5: 启动服务
**开发模式:**
```bash
python3 -m backend.app
```
或者使用 `flask`:
```bash
export FLASK_APP=backend/app.py
flask run --port 5001
```

**生产模式 (Linux/Mac):**
```bash
gunicorn -w 4 -b 0.0.0.0:5001 backend.app:app
```

### 步骤 6: 访问
打开浏览器访问 `http://localhost:5001`。

## 5. 可能的问题与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| **音频合并有杂音或失败** | 缺少 FFmpeg 或 pydub | 安装 FFmpeg 和 `pip install pydub` |
| **TTS 生成失败 (110023 错误)** | 本地时间与服务器时间偏差过大 | 项目已内置时间同步功能，通常会自动修复。若仍失败，检查系统时间或网络连接。 |
| **缓存写入失败** | 权限问题或路径不存在 | 在 `.env` 中设置 `CACHE_DIR` 为当前用户可写的路径 (如 `./cache`)，并确保目录存在。 |
| **API 认证失败** | 未设置 Key 或 Key 不匹配 | 检查 `.env` 中的 `SERVICE_API_KEY`，并在前端界面的设置中填写相同的 Key。 |
| **无法连接上游服务** | 网络限制或防火墙 | 配置 `.env` 中的 `PROXY_URL`，支持 HTTP/HTTPS 代理。 |

## 6. 推荐本地开发工具链
- **IDE**: VS Code (配合 Python 插件)
- **运行环境**: Python 3.10 + venv
- **调试工具**: Postman 或 cURL (用于测试 `/v1/audio/speech` 接口)
