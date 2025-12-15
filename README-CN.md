# NanoAI TTS - 文本转语音服务

[![英文文档](https://img.shields.io/badge/English-README.md-blue?style=flat-square)](./README.md)
[![中文文档](https://img.shields.io/badge/中文-README-CN.md-blue?style=flat-square)](./README-CN.md)
[![部署指南](https://img.shields.io/badge/部署-DEPLOYMENT-green?style=flat-square)](./DEPLOYMENT-CN.md)
[![常见问题](https://img.shields.io/badge/FAQ-常见问题-orange?style=flat-square)](./FAQ-CN.md)

> 一个高性能的文本转语音（TTS）服务，支持多个免费 API 提供商，提供智能 API 降级、无字数限制和丰富的参数控制。

## 📋 目录

- [项目介绍](#项目介绍)
- [核心特性](#核心特性)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [API 文档](#api-文档)
- [环境变量配置](#环境变量配置)
- [常见问题](#常见问题)
- [许可证](#许可证)

## 🎯 项目介绍

**NanoAI TTS** 是一个功能强大的文本转语音服务，基于 Flask 框架开发，支持多个 TTS 提供商。无论是制作视频配音、生成有声书，还是快速浏览长文章，NanoAI TTS 都能帮助你轻松完成。

### 主要亮点

- 🚀 **多提供商支持**：整合 NanoAI、Google、百度、Azure、阿里云等多个 TTS API
- 🔄 **智能降级**：主 API 失败时自动切换到备选 API，确保服务可用性
- 📝 **无字数限制**：支持超长文本生成，自动分段处理
- 🎛️ **丰富参数控制**：调整速度、音调、音量等参数
- 🌍 **多语言支持**：支持中文、英文、日语等多种语言
- 👥 **性别选择**：提供男声、女声、中立声线选项
- ⚡ **高速响应**：优化的缓存和网络连接机制
- 🔐 **安全可靠**：完善的错误处理和日志记录
- 📱 **响应式设计**：支持手机、平板和桌面访问
- ☁️ **云平台部署**：支持 Vercel、Railway、Render 等云平台一键部署

## ✨ 核心特性

### 支持的 TTS 提供商

| 提供商 | 特点 | 语言 | 免费额度 |
|--------|------|------|---------|
| **NanoAI** | 速度快，效果好，中文支持好 | 中文、英文、日语等 | 3000万字符/月 |
| **Google TTS** | 稳定可靠，多语言支持 | 100+ 种语言 | 受限 |
| **百度 TTS** | 中文优化，发音准确 | 中文为主 | 5000万字符/年 |
| **微软 Azure** | 企业级服务，高质量 | 80+ 种语言 | 受限 |
| **阿里云** | 国内服务，速度快 | 中文、英文、日语等 | 受限 |

### 智能 API 降级

```
用户请求 → 尝试 API 1 → 失败? → 尝试 API 2 → 失败? → 尝试 API 3 → 最终返回音频或错误
```

当某个 API 失败时，系统会自动：
1. 记录失败原因（日志）
2. 切换到下一个可用的 API
3. 重试请求
4. 直到成功或所有 API 都失败

### 超长文本处理

对于超长文本，系统会：
1. 自动分段（默认 500 字/段）
2. 分别调用 API 生成音频
3. 自动拼接音频文件
4. 返回完整音频或 ZIP 压缩包

### 缓存机制

- **智能缓存**：相同文本和参数的请求使用缓存，提升速度
- **缓存验证**：定期检查缓存有效性，损坏的缓存自动删除
- **缓存过期**：默认 2 小时过期，可自定义

## 🚀 快速开始

### 在线使用

访问在线演示：https://nami-tts.vercel.app

无需安装，直接在浏览器中使用，支持所有特性。

### 本地运行

#### 前置条件

- Python 3.8 或更高版本
- pip 包管理器
- Git（用于克隆项目）

#### 安装步骤

##### 方式一：使用 Makefile（推荐）

项目提供了 Makefile 来简化本地开发流程：

1. **克隆项目**

```bash
git clone https://github.com/stamns/nami-tts.git
cd nami-tts
```

2. **安装依赖**

```bash
make install
# 或使用: make setup
```

这个命令会自动创建虚拟环境并安装所有依赖。

3. **配置 API Key**

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
nano .env
```

4. **启动服务**

开启两个终端窗口：

```bash
# 终端 1 - 启动后端服务
make dev-backend

# 终端 2 - 启动前端服务
make dev-frontend
```

5. **访问应用**

打开浏览器访问：http://localhost:8000

6. **运行测试**

```bash
make test
# 或使用: make smoke-test
```

##### 方式二：手动安装

1. **克隆项目**

```bash
git clone https://github.com/stamns/nami-tts.git
cd nami-tts
```

2. **创建虚拟环境**

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置 API Key**

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
nano .env
```

示例 `.env` 文件：
```env
# NanoAI API Key (必需)
SERVICE_API_KEY=sk-your-nanoai-key-here

# 可选：其他提供商 API Key
GOOGLE_API_KEY=your-google-key
BAIDU_APP_ID=your-baidu-app-id
BAIDU_API_KEY=your-baidu-api-key
BAIDU_SECRET_KEY=your-baidu-secret

# 服务配置
PORT=5001
DEBUG=False
LOG_LEVEL=INFO

# 网络配置
HTTP_TIMEOUT=60
RETRY_COUNT=2
SSL_VERIFY=true
```

5. **启动服务**

```bash
python3 -m flask --app backend.app run --port=5001
```

6. **访问应用**

打开浏览器访问：http://localhost:5001

##### Makefile 命令参考

项目根目录的 `Makefile` 提供了以下命令：

| 命令 | 说明 |
|------|------|
| `make help` | 显示所有可用命令 |
| `make install` | 创建虚拟环境并安装依赖 |
| `make dev-backend` | 启动 Flask 后端服务（端口：5001） |
| `make dev-frontend` | 启动静态前端服务（端口：8000） |
| `make test` | 运行诊断测试脚本 |
| `make clean` | 清理缓存和构建产物 |
| `make clean-venv` | 删除虚拟环境 |

环境变量可以通过命令行覆盖：

```bash
# 使用自定义端口
BACKEND_PORT=5002 make dev-backend
FRONTEND_PORT=8001 make dev-frontend
```

### Docker 运行

如果你更倾向于使用 Docker：

```bash
# 构建镜像
docker build -t nanoai-tts .

# 运行容器
docker run -p 5001:5001 \
  -e TTS_API_KEY=your-api-key \
  -e PORT=5001 \
  nanoai-tts
```

### Vercel 云部署

最简单的部署方式，1 分钟完成：

1. **Fork 项目**到你的 GitHub 账户

2. **连接到 Vercel**
   - 访问 https://vercel.com
   - 登录/注册账户
   - 点击 "New Project"
   - 选择你 Fork 的仓库

3. **配置环境变量**
   在 Vercel 项目设置中添加：
   - `TTS_API_KEY`: 你的 API Key
   - `HTTP_TIMEOUT`: 60
   - `RETRY_COUNT`: 2

4. **部署**
   点击 "Deploy" 按钮，等待部署完成

详见：[部署指南](./DEPLOYMENT-CN.md)

## 📖 使用指南

### 基本用法

#### Web 界面

1. 输入要转换的文本
2. 选择语言和性别
3. 调整速度、音调、音量等参数
4. 点击生成按钮
5. 等待生成完成，下载音频文件

#### API 调用

使用 cURL 调用 API：

```bash
curl -X POST http://localhost:5001/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "DeepSeek",
    "input": "你好，世界",
    "language": "zh-CN",
    "gender": "female",
    "speed": 1.0,
    "pitch": 1.0,
    "volume": 1.0
  }' \
  --output output.mp3
```

### 参数说明

#### 必需参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `input` | 字符串 | 要转换的文本 | "你好，世界" |
| `model` | 字符串 | TTS 模型/声音 | "DeepSeek" |

#### 可选参数

| 参数 | 类型 | 范围 | 默认值 | 说明 |
|------|------|------|--------|------|
| `speed` | 浮点数 | 0.5-2.0 | 1.0 | 播放速度（0.5=慢, 1.0=正常, 2.0=快） |
| `pitch` | 浮点数 | 0.5-2.0 | 1.0 | 音调（0.5=低, 1.0=正常, 2.0=高） |
| `volume` | 浮点数 | 0.0-1.0 | 1.0 | 音量（0.0=静音, 1.0=最大） |
| `language` | 字符串 | - | zh-CN | 语言代码 |
| `gender` | 字符串 | male/female/neutral | female | 性别 |
| `format` | 字符串 | mp3/wav/ogg | mp3 | 输出格式 |
| `provider` | 字符串 | - | nanoai | 指定 API 提供商 |

#### 语言代码参考

| 代码 | 语言 | 代码 | 语言 |
|------|------|------|------|
| zh-CN | 简体中文 | en-US | 美国英语 |
| zh-TW | 繁体中文 | en-GB | 英国英语 |
| ja-JP | 日语 | ko-KR | 韩语 |
| es-ES | 西班牙语 | fr-FR | 法语 |
| de-DE | 德语 | ru-RU | 俄语 |

### 常见用途示例

#### 1. 制作学习视频配音

```python
import requests

text = "这是一个学习视频的配音文本。"
response = requests.post('http://localhost:5001/v1/audio/speech', json={
    'input': text,
    'model': 'DeepSeek',
    'language': 'zh-CN',
    'gender': 'female',
    'speed': 1.0
})

with open('video_audio.mp3', 'wb') as f:
    f.write(response.content)
```

#### 2. 生成有声书

```python
import requests

# 长文本会自动分段处理
long_text = """
第一章 开始
...（很长的文本）...
第二章 发展
...
"""

response = requests.post('http://localhost:5001/v1/audio/speech', json={
    'input': long_text,
    'model': 'DeepSeek',
    'language': 'zh-CN'
})

# 返回 ZIP 压缩包或 M3U8 播放列表
with open('audiobook.zip', 'wb') as f:
    f.write(response.content)
```

#### 3. 快速浏览长文章

```python
import requests

article = "很长的文章内容..."

response = requests.post('http://localhost:5001/v1/audio/speech', json={
    'input': article,
    'speed': 1.5,  # 加快速度
    'provider': 'nanoai'  # 使用最快的提供商
})

# 播放音频
with open('article_audio.mp3', 'wb') as f:
    f.write(response.content)
```

#### 4. 多语言支持

```python
import requests

# 中文
requests.post('http://localhost:5001/v1/audio/speech', json={
    'input': '你好，世界',
    'language': 'zh-CN'
})

# 英文
requests.post('http://localhost:5001/v1/audio/speech', json={
    'input': 'Hello, world',
    'language': 'en-US'
})

# 日语
requests.post('http://localhost:5001/v1/audio/speech', json={
    'input': 'こんにちは、世界',
    'language': 'ja-JP'
})
```

## 🔌 API 文档

### 基础信息

- **基础 URL**: `http://localhost:5001` (本地) 或 `https://nami-tts.vercel.app` (线上)
- **认证**: 可选 Bearer Token（若 `REQUIRE_AUTH=true`）
- **内容类型**: `application/json`
- **请求限制**: 根据 API 提供商限制

### 端点列表

#### 1. 生成音频

**端点**: `POST /v1/audio/speech`

生成音频文件。

**请求示例**:

```bash
curl -X POST http://localhost:5001/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "DeepSeek",
    "input": "你好，世界",
    "language": "zh-CN",
    "gender": "female",
    "speed": 1.0,
    "pitch": 1.0,
    "volume": 1.0
  }'
```

**请求体**:

```json
{
  "model": "DeepSeek",              // 必需：模型名称
  "input": "要转换的文本",           // 必需：文本内容
  "language": "zh-CN",              // 可选：语言代码
  "gender": "female",               // 可选：性别 (male/female/neutral)
  "speed": 1.0,                     // 可选：速度 (0.5-2.0)
  "pitch": 1.0,                     // 可选：音调 (0.5-2.0)
  "volume": 1.0,                    // 可选：音量 (0.0-1.0)
  "format": "mp3",                  // 可选：格式 (mp3/wav/ogg)
  "provider": "nanoai"              // 可选：指定提供商
}
```

**响应**:

- **成功 (200)**: 返回 MP3 音频文件（二进制）
- **错误 (400-500)**: 返回 JSON 错误信息

**响应头**:

```
Content-Type: audio/mpeg
Content-Length: <size>
X-Audio-Validation: valid
```

#### 2. 获取模型列表

**端点**: `GET /v1/models`

获取可用的 TTS 模型列表。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `provider` | 字符串 | 可选：指定提供商过滤 |
| `language` | 字符串 | 可选：按语言过滤 |

**请求示例**:

```bash
# 所有模型
curl http://localhost:5001/v1/models

# 指定提供商
curl "http://localhost:5001/v1/models?provider=nanoai"

# 指定语言
curl "http://localhost:5001/v1/models?language=zh-CN"
```

**响应示例**:

```json
{
  "models": [
    {
      "id": "DeepSeek",
      "name": "DeepSeek 女声",
      "provider": "nanoai",
      "language": "zh-CN",
      "gender": "female"
    },
    {
      "id": "Qwen",
      "name": "通义千问 女声",
      "provider": "nanoai",
      "language": "zh-CN",
      "gender": "female"
    },
    // ... 更多模型
  ],
  "total": 24
}
```

#### 3. 获取提供商列表

**端点**: `GET /v1/providers`

获取所有 TTS 提供商信息。

**请求示例**:

```bash
curl http://localhost:5001/v1/providers
```

**响应示例**:

```json
{
  "providers": [
    {
      "name": "nanoai",
      "display_name": "NanoAI",
      "available": true,
      "models_count": 10,
      "languages": ["zh-CN", "en-US", "ja-JP"]
    },
    {
      "name": "google",
      "display_name": "Google TTS",
      "available": true,
      "models_count": 5,
      "languages": ["zh-CN", "en-US"]
    },
    // ... 更多提供商
  ],
  "total": 5
}
```

#### 4. 健康检查

**端点**: `GET /health`

检查服务健康状态。

**请求示例**:

```bash
curl http://localhost:5001/health
```

**响应示例**:

```json
{
  "status": "healthy",
  "uptime": 3600,
  "timestamp": "2025-12-15T12:00:00Z",
  "providers": {
    "nanoai": "available",
    "google": "available",
    "baidu": "unavailable"
  },
  "cache": {
    "size": "1.2MB",
    "files": 15,
    "hits": 1200,
    "misses": 300
  }
}
```

#### 5. 诊断信息

**端点**: `GET /v1/audio/diagnose`

获取详细的诊断信息，用于故障排除。

**请求示例**:

```bash
curl http://localhost:5001/v1/audio/diagnose
```

**响应示例**:

```json
{
  "system": {
    "python_version": "3.12.0",
    "platform": "Linux",
    "memory_usage": "145.3 MB"
  },
  "network": {
    "dns_resolution": "ok",
    "api_connectivity": "ok",
    "ssl_verification": "ok"
  },
  "tts_engine": {
    "status": "ready",
    "models_loaded": 24,
    "active_provider": "nanoai",
    "last_error": null
  },
  "cache": {
    "enabled": true,
    "path": "/home/engine/project/cache",
    "size": "1.2MB",
    "integrity": "ok"
  }
}
```

## 🔐 环境变量配置

### 必需变量

至少需要配置一个 TTS 提供商的 API Key。

#### NanoAI (推荐)

```bash
TTS_API_KEY=sk-your-nanoai-key-here
```

获取方式：访问 https://bot.n.cn 注册账户

#### Google TTS (可选)

```bash
GOOGLE_API_KEY=your-google-api-key
GOOGLE_PROJECT_ID=your-project-id
```

获取方式：访问 https://cloud.google.com/docs/authentication/application-default-credentials

### 可选变量

#### 服务配置

```bash
PORT=5001                    # 服务端口（默认 5001）
DEBUG=False                  # 调试模式（生产环境设为 False）
LOG_LEVEL=INFO              # 日志级别 (DEBUG/INFO/WARNING/ERROR)
REQUIRE_AUTH=false          # 是否要求认证（默认 false）
```

#### 网络配置

```bash
HTTP_TIMEOUT=60             # HTTP 请求超时时间（秒）
RETRY_COUNT=2               # API 请求重试次数
PROXY_URL=                  # 代理地址（可选），如 http://proxy:8080
SSL_VERIFY=true             # 是否验证 SSL 证书
```

#### 缓存配置

```bash
CACHE_ENABLED=true          # 是否启用缓存
CACHE_DURATION=7200         # 缓存过期时间（秒）
CACHE_DIR=cache             # 缓存目录路径
MAX_CACHE_SIZE=500          # 最大缓存大小（MB）
```

#### 限流配置

```bash
RATE_LIMIT_ENABLED=false    # 是否启用限流
RATE_LIMIT_PER_MINUTE=60    # 每分钟请求限制
RATE_LIMIT_PER_HOUR=1000    # 每小时请求限制
```

### 完整配置示例

```bash
# .env 文件完整示例
# ============================================

# API 配置（必需）
TTS_API_KEY=sk-your-nanoai-key

# 服务配置
PORT=5001
DEBUG=False
LOG_LEVEL=INFO
REQUIRE_AUTH=false

# 网络配置
HTTP_TIMEOUT=60
RETRY_COUNT=2
SSL_VERIFY=true

# 缓存配置
CACHE_ENABLED=true
CACHE_DURATION=7200
CACHE_DIR=cache

# 时间同步配置（Vercel 部署必需）
TIME_SYNC_ENABLED=true
TIME_SYNC_INTERVAL_SECONDS=300
TIME_SYNC_URL=https://bot.n.cn
TIME_SYNC_USE_SERVER_TIME_ON_DRIFT=true
```

## 🙋 常见问题

### API Key 相关

**Q: 如何获取 NanoAI API Key？**

A: 访问 https://bot.n.cn，注册账户后在设置中获取 API Key。

**Q: 是否必须要 API Key？**

A: 是的，至少需要一个有效的 TTS 提供商 API Key。

**Q: 如何更换 API Key？**

A: 编辑 `.env` 文件中的 `TTS_API_KEY`，重启应用即可。

### 部署相关

**Q: 支持哪些云平台部署？**

A: 支持 Vercel、Railway、Render、Heroku、AWS Lambda 等。详见 [部署指南](./DEPLOYMENT-CN.md)。

**Q: 部署到 Vercel 失败怎么办？**

A: 检查环境变量配置，确保 API Key 正确，查看部署日志中的错误信息。

**Q: 本地和线上部署有什么区别？**

A: 主要区别是网络环境和时间同步配置。线上部署需要时间同步来处理认证问题。

### 使用相关

**Q: 支持多长的文本？**

A: 理论上无限长，但建议单次不超过 10000 字。更长文本会自动分段处理。

**Q: 生成速度慢怎么办？**

A: 可尝试：
1. 缩短文本长度
2. 增加 HTTP_TIMEOUT 值
3. 更换 API 提供商（NanoAI 最快）
4. 启用缓存

**Q: 支持离线使用吗？**

A: 不支持，需要网络连接调用 API。但支持缓存，相同文本会使用本地缓存。

### 故障排除

**Q: 出现 "110023 认证错误" 怎么办？**

A: 通常是时间偏差导致，应用会自动同步时间。如果问题持续，检查 API Key 是否正确。

**Q: 怎样查看详细错误信息？**

A: 设置 `LOG_LEVEL=DEBUG`，查看应用日志或 `/v1/audio/diagnose` 端点。

**Q: 缓存的音频如何删除？**

A: 删除 `cache/` 目录下的相应文件，或设置 `CACHE_DURATION=0` 禁用缓存。

更多问题请见 [常见问题完整版](./FAQ-CN.md)

## 📚 更多资源

- [详细部署指南](./DEPLOYMENT-CN.md) - 多平台部署详细步骤
- [使用示例](./EXAMPLES-CN.md) - 多个实际使用场景
- [常见问题完整版](./FAQ-CN.md) - 更多常见问题和解决方案
- [更新日志](./CHANGELOG-CN.md) - 版本更新历史
- [GitHub 仓库](https://github.com/stamns/nami-tts)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

- GitHub Issues: https://github.com/stamns/nami-tts/issues
- 讨论区: https://github.com/stamns/nami-tts/discussions

---

**最后更新**: 2025年12月15日  
**版本**: 1.0  
**作者**: TTS 开发团队  
**兼容性**: Python 3.8+, Flask 2.3+
