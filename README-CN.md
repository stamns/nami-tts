# NanoAI TTS - 文本转语音服务

[![英文文档](https://img.shields.io/badge/English-README.md-blue?style=flat-square)](./README.md)
[![中文文档](https://img.shields.io/badge/中文-README-CN.md-blue?style=flat-square)](./README-CN.md)
[![部署指南](https://img.shields.io/badge/部署-DEPLOYMENT-green?style=flat-square)](./DEPLOYMENT-CN.md)
[![常见问题](https://img.shields.io/badge/FAQ-常见问题-orange?style=flat-square)](./FAQ-CN.md)

> 一个高性能的文本转语音（TTS）服务，支持多个免费 API 提供商，提供智能 API 降级、无字数限制和丰富的参数控制。

## 📋 目录

1. [项目介绍](#1-项目介绍)
2. [快速开始](#2-快速开始)
3. [系统要求](#3-系统要求)
4. [详细部署指南](#4-详细部署指南)
5. [环境变量配置指南](#5-环境变量配置指南)
6. [Makefile 命令速查表](#6-makefile-命令速查表)
7. [项目架构](#7-项目架构)
8. [API 使用指南](#8-api-使用指南)
9. [常见问题和故障排查](#9-常见问题和故障排查)
10. [贡献指南](#10-贡献指南)
11. [许可证和联系方式](#11-许可证和联系方式)

---

## 1. 项目介绍

**NanoAI TTS** 是一个功能强大的文本转语音服务，基于 Flask 框架开发。无论是制作视频配音、生成有声书，还是快速浏览长文章，NanoAI TTS 都能帮助你轻松完成。

### 核心功能特性

- 🚀 **多提供商支持**：整合 NanoAI、Google、百度、Azure、阿里云等多个 TTS API。
- 🔄 **智能降级**：主 API 失败时自动切换到备选 API，确保服务高可用。
- 📝 **无字数限制**：支持超长文本生成，自动分段处理和拼接。
- 🎛️ **丰富参数控制**：精细调整语速、音调、音量、格式（MP3/WAV/OGG）。
- 🌍 **多语言支持**：支持中文、英文、日语、德语等多种语言。
- ⚡ **高速缓存**：智能缓存机制，大幅提升响应速度。
- ☁️ **云原生友好**：完美支持 Vercel 等 Serverless 平台部署。

### 应用场景

- **内容创作**：短视频配音、播客制作。
- **辅助阅读**：有声书生成、文章朗读。
- **教育培训**：语言学习素材制作。
- **智能客服**：语音交互系统的合成引擎。

---

## 2. 快速开始

### 🏠 本地部署（3步快速开始）

1. **克隆并安装**
   ```bash
   git clone https://github.com/stamns/nami-tts.git
   cd nami-tts
   make install
   ```

2. **配置环境**
   ```bash
   cp .env.example .env
   # 至少设置 SERVICE_API_KEY
   ```

3. **启动服务**
   ```bash
   make dev-backend
   # 另开终端：make dev-frontend
   ```

### ☁️ Vercel 部署（3步快速开始）

1. **Fork 本仓库**到你的 GitHub 账号。
2. **在 Vercel 导入项目**，并在 Settings > Environment Variables 中添加：
   - `SERVICE_API_KEY`: 你的密钥
3. **点击 Deploy**，等待部署完成。

---

## 3. 系统要求

- **Python**: 3.8 或更高版本
- **包管理器**: pip
- **Git**: 用于版本控制
- **操作系统**: 
  - Linux / macOS (推荐)
  - Windows (建议使用 WSL 或 Git Bash)
- **可选依赖**: FFmpeg (用于更高级的音频处理，非必需)
- **磁盘空间**: 至少 500MB (用于依赖和缓存)

---

## 4. 详细部署指南

### 4.1 本地部署

#### 前置条件检查
确保终端中可以运行 `python3 --version` 和 `git --version`。

#### 步骤 1: 克隆项目
```bash
git clone https://github.com/stamns/nami-tts.git
cd nami-tts
```

#### 步骤 2: 安装依赖
使用 Makefile 一键安装：
```bash
make install
```
此命令会自动创建 `.venv` 虚拟环境并安装 `requirements.txt` 中的依赖。

#### 步骤 3: 配置环境变量
```bash
cp .env.example .env
```
编辑 `.env` 文件，重点配置 `SERVICE_API_KEY`。如果需要使用其他 TTS 提供商，请填入相应的 API Key。

#### 步骤 4: 启动后端服务
```bash
make dev-backend
```
服务将在 `http://localhost:5001` 启动。

#### 步骤 5: 启动前端界面
打开新的终端窗口，运行：
```bash
make dev-frontend
```
访问 `http://localhost:8000` 即可使用 Web 界面。

#### 停止服务
在终端中按 `Ctrl+C` 停止服务。

### 4.2 Vercel 部署

#### 步骤 1: 准备 GitHub 仓库
Fork 本项目到你的 GitHub 账户。

#### 步骤 2: 创建 Vercel 项目
1. 登录 [Vercel](https://vercel.com)。
2. 点击 **Add New...** -> **Project**。
3. 选择你刚才 Fork 的 `nami-tts` 仓库。

#### 步骤 3: 配置环境变量
在 **Environment Variables** 区域，添加以下变量：

| 变量名 | 描述 | 示例值 |
|--------|------|--------|
| `SERVICE_API_KEY` | 服务认证密钥（必需） | `sk-your-secret-key` |
| `CACHE_DIR` | 缓存目录（Serverless 环境必需） | `/tmp/cache` |

> **注意**: Vercel Serverless 环境只有 `/tmp` 目录是可写的，务必设置 `CACHE_DIR=/tmp/cache`。

#### 步骤 4: 部署
点击 **Deploy**。部署完成后，Vercel 会提供一个访问域名（如 `https://your-project.vercel.app`）。

#### 步骤 5: 绑定自定义域名 (可选)
在 Vercel 项目 Settings > Domains 中配置你的自定义域名。

---

## 5. 环境变量配置指南

详细说明 `.env` 文件中的关键配置项。

### 服务认证
- `SERVICE_API_KEY`: API 调用的认证密钥（Bearer Token）。
  - 示例: `sk-a1b2c3d4e5`
  - 旧版本兼容名: `TTS_API_KEY`

### TTS 提供商凭证
根据你需要使用的提供商配置：
- `GOOGLE_API_KEY`: Google Cloud TTS Key (可选)
- `AZURE_API_KEY`: Azure Speech Key (可选)
- `AZURE_REGION`: Azure 区域 (如 `eastus`)
- `BAIDU_API_KEY` / `BAIDU_SECRET_KEY`: 百度语音 Key (可选)

### 网络和缓存配置
- `HTTP_TIMEOUT`: 请求超时时间（秒），默认 `30`。
- `RETRY_COUNT`: 失败重试次数，默认 `2`。
- `CACHE_DIR`: 音频缓存路径。
  - 本地建议: `cache` (默认)
  - Vercel 建议: `/tmp/cache`
- `MODELS_CACHE_TTL_SECONDS`: 模型列表缓存时间，默认 `7200` (2小时)。

### 时间同步 (Vercel 专用)
- `TIME_SYNC_ENABLED`: `true` (默认)，解决 Serverless 环境时间漂移问题。

---

## 6. Makefile 命令速查表

项目根目录提供了 `Makefile` 以简化开发流程：

| 命令 | 说明 |
|------|------|
| `make install` | 创建虚拟环境并安装所有依赖 |
| `make dev-backend` | 启动 Flask 后端服务 (端口 5001) |
| `make dev-frontend` | 启动静态前端服务 (端口 8000) |
| `make test` | 运行诊断和冒烟测试 |
| `make clean` | 清理缓存和构建文件 |
| `make clean-venv` | 删除虚拟环境 |
| `make help` | 显示所有可用命令帮助 |

---

## 7. 项目架构

### 目录结构
```
nami-tts/
├── backend/            # 后端代码
│   ├── app.py          # Flask 应用入口
│   ├── nano_tts.py     # TTS 引擎核心逻辑
│   ├── config.py       # 配置管理
│   └── utils/          # 工具函数 (音频处理、日志)
├── frontend/           # 前端代码
│   └── index.html      # 单页应用界面
├── docs/               # 文档目录
├── tests/              # 测试脚本
├── .env.example        # 环境变量模板
├── Makefile            # 任务运行器
└── vercel.json         # Vercel 部署配置
```

### 数据流
1. **用户请求**: 前端/API 发送文本和参数。
2. **路由处理**: `app.py` 接收请求并进行鉴权。
3. **TTS 引擎**: `nano_tts.py` 根据优先级选择 TTS 提供商。
4. **外部调用**: 调用第三方 API (NanoAI, Google, Azure 等)。
5. **音频处理**: 验证、标准化和格式转换。
6. **响应返回**: 返回音频流或 JSON 错误信息。

---

## 8. API 使用指南

### 认证方式
所有受保护的端点都需要在 Header 中携带 Bearer Token：
```http
Authorization: Bearer <YOUR_SERVICE_API_KEY>
```

### 主要 API 端点

#### 1. 生成语音
- **URL**: `POST /v1/audio/speech`
- **说明**: 将文本转换为语音。
- **请求体**:
  ```json
  {
    "model": "DeepSeek",
    "input": "你好，世界",
    "voice": "alloy",
    "speed": 1.0
  }
  ```
- **响应**: 音频文件流 (audio/mpeg)。

#### 2. 获取模型列表
- **URL**: `GET /v1/models`
- **说明**: 获取当前可用 TTS 模型列表。
- **响应**:
  ```json
  {
    "data": [
      {"id": "DeepSeek", "owned_by": "nanoai"}
    ]
  }
  ```

#### 3. 获取提供商列表
- **URL**: `GET /v1/providers`
- **说明**: 查看配置的提供商及其健康状态。

#### 4. 安全配置更新
- **URL**: `PUT /v1/ui/config/secure`
- **说明**: 更新 UI 配置（需要认证）。
- **请求体**:
  ```json
  {
    "config": { ... }
  }
  ```

### 示例请求 (cURL)
```bash
curl -X POST http://localhost:5001/v1/audio/speech \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "DeepSeek",
    "input": "Hello World",
    "speed": 1.0
  }' \
  --output speech.mp3
```

---

## 9. 常见问题和故障排查

### 🔴 端口被占用
**现象**: `Address already in use` 错误。
**解决**: 修改 `.env` 中的 `PORT` 变量，或使用命令 `BACKEND_PORT=5002 make dev-backend`。

### 🔴 API 认证失败 (401)
**现象**: 返回 `{"error": "Invalid API Key"}`。
**解决**: 
1. 检查 `.env` 文件中 `SERVICE_API_KEY` 是否设置。
2. 确认请求头中包含 `Authorization: Bearer <key>`。
3. 检查是否有空格或特殊字符。

### 🔴 缓存目录权限问题
**现象**: `Permission denied` 写入缓存失败。
**解决**: 
- 本地运行: `chmod -R 755 cache`。
- Vercel: 确保配置 `CACHE_DIR=/tmp/cache`。

### 🔴 TTS 引擎加载失败
**现象**: 日志显示 `Provider initialization failed`。
**解决**: 检查对应提供商的 API Key 是否正确配置。

---

## 10. 贡献指南

我们非常欢迎社区贡献！

### 开发环境设置
参考 [详细部署指南](#4-详细部署指南) 中的本地部署步骤。

### 代码风格
- Python 代码遵循 PEP 8 规范。
- 提交前请运行 `make test` 确保所有检查通过。

### 提交 PR 流程
1. Fork 本仓库。
2. 创建新分支: `git checkout -b feature/amazing-feature`。
3. 提交更改: `git commit -m 'Add amazing feature'`。
4. 推送到分支: `git push origin feature/amazing-feature`。
5. 提交 Pull Request。

---

## 11. 许可证和联系方式

### 许可证
本项目采用 **MIT License** 开源授权。详见 [LICENSE](LICENSE) 文件。

### 联系方式
- **GitHub Issues**: 提交 Bug 或建议
- **Email**: support@nanoai.com (示例)

---
*文档最后更新时间: 2025年12月*
