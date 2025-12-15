# 部署指南 - NanoAI TTS 服务部署

[![返回 README](https://img.shields.io/badge/返回-README--CN-blue?style=flat-square)](./README-CN.md)
[![FAQ](https://img.shields.io/badge/常见问题-FAQ--CN-orange?style=flat-square)](./FAQ-CN.md)

本指南详细说明如何在各个平台部署 NanoAI TTS 服务。

## 📋 目录

- [前置要求](#前置要求)
- [本地开发部署](#本地开发部署)
- [Vercel 部署（推荐）](#vercel-部署推荐)
- [Docker 部署](#docker-部署)
- [Railway 部署](#railway-部署)
- [Render 部署](#render-部署)
- [传统服务器部署](#传统服务器部署)
- [环境变量配置](#环境变量配置)
- [故障排查](#故障排查)
- [性能优化](#性能优化)
- [监控和维护](#监控和维护)

## ✅ 前置要求

### 系统要求

- **操作系统**: Linux、macOS 或 Windows
- **Python 版本**: 3.8 或更高（推荐 3.10+）
- **内存**: 最少 256MB（推荐 512MB+）
- **磁盘空间**: 最少 200MB（包含缓存）

### 必要条件

- Git（用于克隆项目）
- pip（Python 包管理器）
- 至少一个 TTS API 的密钥（NanoAI、Google、百度等）

### 验证环境

```bash
# 检查 Python 版本
python3 --version

# 检查 pip
pip3 --version

# 检查 Git
git --version
```

## 🏠 本地开发部署

### 第一步：克隆项目

```bash
# 克隆仓库
git clone https://github.com/stamns/nami-tts.git
cd nami-tts

# 或使用 SSH
git clone git@github.com:stamns/nami-tts.git
cd nami-tts
```

### 第二步：设置虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# 验证虚拟环境激活（命令行前缀应显示 (venv)）
```

### 第三步：安装依赖

```bash
# 升级 pip（可选但推荐）
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

### 第四步：配置环境变量

```bash
# 复制示例环境文件
cp .env.example .env

# 编辑 .env 文件（使用你喜欢的编辑器）
nano .env
```

在 `.env` 中添加你的 API Key：

```env
# NanoAI API Key（必需）
TTS_API_KEY=sk-your-nanoai-api-key

# 服务配置
PORT=5001
DEBUG=False
LOG_LEVEL=INFO

# 网络配置（可选）
HTTP_TIMEOUT=60
RETRY_COUNT=2
SSL_VERIFY=true
```

### 第五步：启动服务

```bash
# 启动应用
python3 app.py

# 输出应样类似：
# * Running on http://127.0.0.1:5001
# * Press CTRL+C to quit
```

### 第六步：验证部署

打开浏览器访问：http://localhost:5001

或使用 curl 测试 API：

```bash
curl -X POST http://localhost:5001/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "DeepSeek",
    "input": "你好，世界",
    "language": "zh-CN"
  }' \
  --output test.mp3

# 检查音频文件是否成功生成
file test.mp3
```

## ☁️ Vercel 部署（推荐）

Vercel 是部署此应用的最简单方式，支持自动部署和 CI/CD。

### 前置条件

- GitHub 账户
- Vercel 账户（https://vercel.com，可用 GitHub 账户登录）

### 部署步骤

#### 第一步：Fork 项目

访问 https://github.com/stamns/nami-tts 并点击 "Fork" 按钮。

#### 第二步：导入到 Vercel

1. 登录 https://vercel.com
2. 点击 "New Project"
3. 选择 "Import Git Repository"
4. 输入你的 fork 仓库 URL
5. 点击 "Import"

#### 第三步：配置环境变量

在 Vercel 的项目设置中，进入 "Environment Variables" 并添加：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `TTS_API_KEY` | `sk-...` | 你的 NanoAI API Key |
| `HTTP_TIMEOUT` | `60` | HTTP 超时时间 |
| `RETRY_COUNT` | `2` | 重试次数 |
| `DEBUG` | `False` | 关闭调试模式 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

**完整配置示例**:

```
TTS_API_KEY=sk-your-api-key-here
HTTP_TIMEOUT=60
RETRY_COUNT=2
DEBUG=False
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
```

#### 第四步：部署

点击 "Deploy" 按钮开始部署。部署通常需要 1-2 分钟。

#### 第五步：验证部署

部署成功后：

1. Vercel 会提供一个部署 URL（通常为 `https://<project-name>.vercel.app`）
2. 访问该 URL 测试应用
3. 测试 API 端点

```bash
# 替换为你的 Vercel URL
curl https://your-project-name.vercel.app/health
```

### 更新部署

```bash
# 在本地更新代码后，推送到 GitHub
git push origin main

# Vercel 会自动检测更新并重新部署
```

### Vercel 特殊配置

Vercel 环境有一些特殊限制，`vercel.json` 中已包含必要配置：

```json
{
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "PYTHONUNBUFFERED": "1",
    "TIME_SYNC_ENABLED": "true",
    "TIME_DRIFT_THRESHOLD_SECONDS": "30",
    "TIME_SYNC_INTERVAL_SECONDS": "300",
    "TIME_SYNC_URL": "https://bot.n.cn",
    "TIME_SYNC_USE_SERVER_TIME_ON_DRIFT": "true"
  }
}
```

**注意事项**:
- Vercel 环境不允许配置系统时区，代码已使用时间同步机制处理
- 无状态设计，不支持本地文件系统持久化（每次部署都会清除缓存）
- 支持最多 12 秒的函数执行时间

## 🐳 Docker 部署

### 前置条件

- Docker 已安装（https://docs.docker.com/install/）
- Docker Compose（可选）

### 使用现有 Dockerfile

项目已包含 Dockerfile，可直接使用：

```bash
# 构建镜像
docker build -t nanoai-tts:latest .

# 运行容器
docker run -p 5001:5001 \
  -e TTS_API_KEY=sk-your-api-key \
  -e HTTP_TIMEOUT=60 \
  -e DEBUG=False \
  nanoai-tts:latest
```

### Docker Compose 部署

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  tts:
    build: .
    container_name: nanoai-tts
    ports:
      - "5001:5001"
    environment:
      TTS_API_KEY: ${TTS_API_KEY}
      PORT: 5001
      DEBUG: False
      LOG_LEVEL: INFO
      HTTP_TIMEOUT: 60
      RETRY_COUNT: 2
    volumes:
      - ./cache:/home/engine/project/cache
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

部署命令：

```bash
# 创建 .env 文件
echo "TTS_API_KEY=sk-your-api-key" > .env

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### Docker 最佳实践

```bash
# 查看运行中的容器
docker ps

# 查看容器日志
docker logs -f nanoai-tts

# 进入容器进行调试
docker exec -it nanoai-tts bash

# 清理未使用的镜像
docker image prune -a

# 备份缓存数据
docker cp nanoai-tts:/home/engine/project/cache ./backup/cache
```

## 🚂 Railway 部署

Railway 是另一个简单的云平台，支持自动部署。

### 部署步骤

1. **访问 Railway**
   - 打开 https://railway.app
   - 用 GitHub 账户登录

2. **新建项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你 Fork 的 nami-tts 仓库

3. **配置环境变量**
   在项目设置中添加：
   ```
   TTS_API_KEY=sk-your-api-key
   PYTHON_VERSION=3.12
   ```

4. **部署**
   - Railway 会自动检测并部署应用
   - 通常需要 3-5 分钟

5. **获取 URL**
   - 部署完成后，Railway 会生成一个公开 URL
   - 可在项目设置中添加自定义域名

## 🎨 Render 部署

Render 提供免费层级的部署服务。

### 部署步骤

1. **访问 Render**
   - 打开 https://render.com
   - 用 GitHub 账户登录

2. **创建 Web Service**
   - 点击 "New" → "Web Service"
   - 连接你的 GitHub 仓库
   - 选择 nami-tts 项目

3. **配置构建和启动**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

4. **设置环境变量**
   在 "Environment" 标签中添加：
   ```
   TTS_API_KEY=sk-your-api-key
   PORT=5000
   ```

5. **部署**
   - 点击 "Create Web Service"
   - Render 会自动构建和部署

## 🖥️ 传统服务器部署

### Linux VPS 部署（以 Ubuntu 为例）

#### 第一步：系统更新

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx supervisor
```

#### 第二步：克隆项目

```bash
cd /home/ubuntu
git clone https://github.com/stamns/nami-tts.git
cd nami-tts
```

#### 第三步：设置应用

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建 .env 文件
cp .env.example .env
nano .env  # 添加你的 API Key
```

#### 第四步：配置 Supervisor

创建 `/etc/supervisor/conf.d/nanoai-tts.conf`：

```ini
[program:nanoai-tts]
directory=/home/ubuntu/nami-tts
command=/home/ubuntu/nami-tts/venv/bin/gunicorn --bind 127.0.0.1:5001 --workers 4 app:app
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/nanoai-tts.err.log
stdout_logfile=/var/log/nanoai-tts.out.log
environment=PATH="/home/ubuntu/nami-tts/venv/bin"
```

#### 第五步：启动服务

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start nanoai-tts
```

#### 第六步：配置 Nginx

创建 `/etc/nginx/sites-available/nanoai-tts`：

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }

    # 健康检查端点（不计日志）
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:5001;
    }
}
```

启用网站：

```bash
sudo ln -s /etc/nginx/sites-available/nanoai-tts /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 第七步：配置 SSL 证书（Let's Encrypt）

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

#### 第八步：验证部署

```bash
# 检查应用运行状态
sudo supervisorctl status nanoai-tts

# 查看应用日志
tail -f /var/log/nanoai-tts.out.log

# 测试应用
curl https://your-domain.com/health
```

## 🔧 环境变量配置

### 必需变量

```bash
# TTS API Key（至少一个）
TTS_API_KEY=sk-your-nanoai-key
```

### 常用变量

```bash
# 服务配置
PORT=5001
DEBUG=False
LOG_LEVEL=INFO

# 网络配置
HTTP_TIMEOUT=60
RETRY_COUNT=2
PROXY_URL=
SSL_VERIFY=true

# 缓存配置
CACHE_ENABLED=true
CACHE_DURATION=7200
CACHE_DIR=cache
```

### 完整配置参考

```bash
# 基础配置
PORT=5001
DEBUG=False
LOG_LEVEL=INFO
REQUIRE_AUTH=false

# API 配置
TTS_API_KEY=sk-your-key

# 网络配置
HTTP_TIMEOUT=60
RETRY_COUNT=2
PROXY_URL=
SSL_VERIFY=true

# 缓存配置
CACHE_ENABLED=true
CACHE_DURATION=7200
CACHE_DIR=cache
MAX_CACHE_SIZE=500

# 时间同步配置（Vercel 等云平台需要）
TIME_SYNC_ENABLED=true
TIME_SYNC_INTERVAL_SECONDS=300
TIME_SYNC_URL=https://bot.n.cn
TIME_SYNC_USE_SERVER_TIME_ON_DRIFT=true

# 日志配置
LOG_FILE=logs/app.log
LOG_LEVEL=INFO
```

## 🐛 故障排查

### 常见问题

#### 问题 1：API Key 认证失败

**症状**: 返回 "110023 认证错误"

**解决步骤**:

1. 验证 API Key 是否正确
   ```bash
   echo $TTS_API_KEY
   ```

2. 检查环境变量是否正确加载
   ```bash
   # 访问诊断端点
   curl http://your-domain.com/v1/audio/diagnose
   ```

3. 尝试重启应用
   ```bash
   # Docker 方式
   docker-compose restart tts
   
   # Vercel 方式：推送新的提交来触发重新部署
   ```

#### 问题 2：端口被占用

**症状**: `Address already in use`

**解决**:

```bash
# 查找占用端口 5001 的进程
lsof -i :5001

# 关闭进程（替换 PID）
kill -9 <PID>

# 或更改端口
export PORT=5002
```

#### 问题 3：内存不足

**症状**: 应用经常被杀死或响应缓慢

**解决**:

1. 增加服务器内存
2. 减少 Worker 数量
3. 启用缓存来减少 API 调用

```bash
# Gunicorn workers 配置
gunicorn --workers 2 app:app  # 减少 workers
```

#### 问题 4：SSL 证书错误

**症状**: `SSL: CERTIFICATE_VERIFY_FAILED`

**解决**:

```bash
# 开发环境临时禁用（仅开发）
export SSL_VERIFY=false

# 生产环境检查证书
openssl s_client -connect bot.n.cn:443
```

#### 问题 5：缓存问题

**症状**: 音频生成结果不一致或缓存文件损坏

**解决**:

```bash
# 清理缓存
rm -rf cache/*

# 或者禁用缓存
export CACHE_ENABLED=false
```

### 调试模式

启用详细日志进行故障排除：

```bash
# 设置日志级别
export LOG_LEVEL=DEBUG

# 查看实时日志
tail -f logs/app.log

# 运行诊断端点
curl http://localhost:5001/v1/audio/diagnose | jq
```

## ⚡ 性能优化

### 1. 缓存优化

```bash
# 启用缓存
CACHE_ENABLED=true
CACHE_DURATION=7200      # 2 小时

# 定期清理过期缓存
find cache/ -type f -mtime +1 -delete
```

### 2. 网络优化

```bash
# 调整超时和重试
HTTP_TIMEOUT=60          # 生产环境
RETRY_COUNT=2

# 使用连接池（已内置）
```

### 3. 并发优化

```bash
# Gunicorn workers 数量
# 推荐：2 * CPU_CORES + 1
gunicorn --workers 4 --threads 2 app:app
```

### 4. 监控性能

```bash
# 检查内存使用
free -h

# 监控 CPU 使用
top

# 查看网络连接
netstat -an | grep ESTABLISHED | wc -l
```

## 📊 监控和维护

### 健康检查

```bash
# 定期检查健康状态
curl http://your-domain.com/health

# 设置监控告警（使用 cron）
*/5 * * * * curl -f http://your-domain.com/health || mail -s "TTS Service Down" admin@example.com
```

### 日志管理

```bash
# 查看最近日志
tail -50 /var/log/nanoai-tts.out.log

# 搜索错误
grep "ERROR" /var/log/nanoai-tts.err.log

# 按日期查看日志
journalctl -u nanoai-tts --since "2025-12-15 10:00:00"
```

### 备份

```bash
# 备份缓存
tar -czf cache_backup_$(date +%Y%m%d).tar.gz cache/

# 备份日志
tar -czf logs_backup_$(date +%Y%m%d).tar.gz /var/log/nanoai-tts*

# 定期备份（cron）
0 2 * * * cd /home/ubuntu/nami-tts && tar -czf ~/backups/cache_backup_$(date +\%Y\%m\%d).tar.gz cache/
```

### 更新应用

```bash
# 拉取最新代码
git pull origin main

# 重启应用
sudo supervisorctl restart nanoai-tts

# Vercel 自动更新（推送到 GitHub 即可）
```

## 📋 部署检查清单

部署前检查：

- [ ] API Key 已获取并验证
- [ ] 环境变量正确配置
- [ ] 依赖已安装
- [ ] 本地测试通过
- [ ] 日志级别设为 INFO（生产环境）
- [ ] DEBUG 设为 False（生产环境）

部署后检查：

- [ ] 应用正常启动
- [ ] `/health` 端点返回 healthy
- [ ] `/v1/models` 端点可访问
- [ ] `/v1/audio/speech` 端点能成功生成音频
- [ ] `/v1/audio/diagnose` 端点显示所有检查通过
- [ ] SSL 证书有效（如适用）
- [ ] 日志记录正常

---

**最后更新**: 2025年12月15日  
**版本**: 1.0  
**兼容性**: Python 3.8+
