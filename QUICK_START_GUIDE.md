# 快速开始指南

## 🚀 5 分钟快速部署

### 前置条件检查
```bash
# 确认 Python 版本 (3.8+)
python3 --version

# 确认拥有项目目录访问权限
cd /path/to/nami-tts
```

### 安装和启动

#### 方案 A: 使用 Makefile（推荐 ⭐）

```bash
# 1. 安装依赖 (~30 秒)
make install

# 2. 创建配置文件
cp .env.example .env

# 3. 启动后端 (在终端 1)
make dev-backend
# 输出: Running on http://127.0.0.1:5001

# 4. 启动前端 (在终端 2)
make dev-frontend
# 输出: Serving on http://127.0.0.1:8000

# 5. 打开浏览器
# 访问: http://localhost:8000
```

#### 方案 B: 手动安装

```bash
# 1. 创建虚拟环境
python3 -m venv .venv

# 2. 激活虚拟环境
source .venv/bin/activate      # Linux/macOS
# 或
.venv\Scripts\activate          # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境
cp .env.example .env

# 5. 启动后端
python -m flask --app backend.app run --port=5001

# 6. 启动前端 (另开一个终端)
cd frontend
python -m http.server 8000
```

---

## 📋 Makefile 常用命令

| 命令 | 说明 | 用途 |
|------|------|------|
| `make help` | 显示所有可用命令 | 查看帮助 |
| `make install` | 创建虚拟环境 + 安装依赖 | 首次安装 |
| `make dev-backend` | 启动 Flask 后端服务 | 本地开发 |
| `make dev-frontend` | 启动前端开发服务器 | 本地开发 |
| `make test` | 运行诊断测试 | 验证功能 |
| `make clean` | 清理所有缓存 | 清理项目 |
| `make clean-venv` | 删除虚拟环境 | 重新安装 |

---

## 🔧 常见问题

### Q: 后端启动失败，提示"Address already in use"

**A:** 端口被占用，更改端口：
```bash
BACKEND_PORT=5002 make dev-backend
```

### Q: 前端无法连接到后端 API

**A:** 在前端页面的"API 选择"部分配置：
1. 点击"API 选择"选项卡
2. 在"API Base"输入框填入: `http://localhost:5001`
3. 点击"保存配置"

### Q: Make 命令无法识别（Windows 用户）

**A:** 使用以下方法之一：
```bash
# 方法 1: 使用 Git Bash
bash -c "make install"

# 方法 2: 使用 WSL
wsl make install

# 方法 3: 指定 Python 路径
make PYTHON=python install
```

### Q: 导入错误："No module named 'backend'"

**A:** 确保虚拟环境已激活：
```bash
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate          # Windows
```

### Q: API Key 配置问题

**A:** 检查 `.env` 文件：
```bash
# 最小配置（本地测试）
SERVICE_API_KEY=sk-nami-tts-your-secret-key
PORT=5001
DEBUG=false

# 其他 API Key 可选（可留空）
GOOGLE_API_KEY=
AZURE_API_KEY=
```

---

## 📊 验证部署成功

运行以下命令验证所有组件：

```bash
# 后端已启动
curl -s http://localhost:5001/v1/models | head -c 50
# 应该看到: {"data":[{"created":...

# 前端已启动
curl -s http://localhost:8000/ | head -c 50
# 应该看到: <!DOCTYPE html>

# 运行诊断
make test
# 应该看到: ✅ 通过的测试项
```

---

## 🌐 访问应用

- **Web UI**: http://localhost:8000
- **API 文档**: http://localhost:5001/v1/models
- **诊断信息**: http://localhost:5001/v1/audio/diagnose

---

## 📚 更多信息

- 详细部署指南: [DEPLOYMENT-CN.md](./DEPLOYMENT-CN.md)
- 常见问题解答: [FAQ-CN.md](./FAQ-CN.md)
- API 使用示例: [EXAMPLES-CN.md](./EXAMPLES-CN.md)
- 完整验证报告: [LOCAL_DEPLOYMENT_VERIFICATION_REPORT.md](./LOCAL_DEPLOYMENT_VERIFICATION_REPORT.md)

---

## 🎯 下一步

1. **配置 API Key**
   - 编辑 `.env` 文件
   - 添加你的 NanoAI API Key（可选其他提供商）

2. **测试 TTS 功能**
   - 访问 http://localhost:8000
   - 输入文本并生成语音
   - 尝试不同的语音和语言选项

3. **查看 API 文档**
   - 学习如何集成到你的应用
   - 参考 EXAMPLES-CN.md 中的代码示例

---

## 💡 性能提示

### 后端性能优化

```bash
# 启用 DEBUG 模式（开发时）
DEBUG=true make dev-backend

# 增加缓存时间
MODELS_CACHE_TTL_SECONDS=3600 make dev-backend
```

### 前端性能优化

```bash
# 使用指定的前端端口
FRONTEND_PORT=8080 make dev-frontend
```

---

## 🔒 安全建议

### 生产部署

```bash
# 关闭 DEBUG 模式
DEBUG=false

# 使用强 API Key
SERVICE_API_KEY=sk-$(openssl rand -hex 32)

# 启用 SSL
SSL_VERIFY=true

# 配置代理（如需要）
PROXY_URL=http://proxy-server:port
```

### 本地开发

```bash
# 使用默认 API Key（仅用于开发）
SERVICE_API_KEY=sk-nami-tts-dev-key

# 启用日志
LOG_LEVEL=DEBUG
```

---

**祝你部署顺利！如有问题，请查看 [FAQ-CN.md](./FAQ-CN.md) 或提交 Issue。**
