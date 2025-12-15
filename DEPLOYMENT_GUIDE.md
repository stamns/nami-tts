# TTS 服务部署指南 - bot.n.cn API 连接问题修复

## 概述

本指南详细说明了修复 TTS 服务在部署环境中无法连接 bot.n.cn API 的问题和相关改进。

## 问题描述

- **现象**: 部署后 TTS 服务无法正常生成音频，本地正常但服务器上返回 JSON 错误响应
- **错误**: `first16=7b22636f6465223a3131303032332c22` (解码后为 JSON: `{"code":"110023"...}`)
- **根因**: 部署环境的网络连接问题、API认证问题或请求配置问题

## 修复内容

### 1. 网络连接优化

#### 新增环境配置
```bash
# .env 文件新增配置
HTTP_TIMEOUT=60        # HTTP请求超时时间(秒)
RETRY_COUNT=2          # API请求重试次数
PROXY_URL=             # HTTP代理地址，如: http://proxy.company.com:8080
SSL_VERIFY=true        # 是否验证SSL证书，生产环境建议设为true
CACHE_DIR=cache        # 缓存目录路径
```

#### 代理支持
- 支持通过 `PROXY_URL` 配置 HTTP/HTTPS 代理
- 在企业网络环境中可以指定代理服务器

#### SSL/TLS 配置
- 可通过 `SSL_VERIFY=false` 禁用SSL证书验证（开发环境）
- 生产环境建议保持 `SSL_VERIFY=true`

### 2. 错误处理和重试机制

#### 智能重试策略
```python
# 实现了智能重试机制
- 客户端错误(4xx): 不重试，直接返回错误
- 服务器错误(5xx): 自动重试，最多3次
- 网络错误: 指数退避重试
- 超时错误: 延长超时时间后重试
```

#### 详细错误诊断
- 解析 API 返回的 JSON 错误信息
- 根据错误代码提供具体的解决方案
- 记录详细的请求和响应日志

### 3. 诊断端点

#### 新增 `/v1/audio/diagnose` 端点
提供全面的网络和 API 连接诊断：

**测试项目**:
- DNS 解析测试
- 基础网络连接测试
- API 端点连通性测试
- SSL/TLS 证书验证
- 缓存状态检查
- 响应时间测量

**使用方法**:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:5001/v1/audio/diagnose
```

#### 改进的健康检查端点
- 检查 TTS 引擎初始化状态
- 验证模型缓存可用性
- 显示详细的配置信息

### 4. 容错机制

#### 缓存策略改进
- 验证缓存文件格式完整性
- 网络失败时自动使用缓存数据
- 缓存损坏时自动重新获取

#### 优雅降级
- API 不可用时提供详细的错误信息
- 网络问题时的自动重试机制
- 支持离线模式的缓存回退

## 部署配置

### 环境变量配置

#### 必需配置
```bash
# API 认证
TTS_API_KEY=your_actual_api_key_here

# 基础配置
PORT=5001
DEBUG=False
LOG_LEVEL=INFO
```

#### 网络优化配置
```bash
# 网络连接
HTTP_TIMEOUT=60        # 生产环境建议设置为60秒
RETRY_COUNT=2          # 重试次数
PROXY_URL=             # 如果需要代理，设置这里
SSL_VERIFY=true        # 生产环境保持true

# 缓存配置
CACHE_DURATION=7200    # 缓存时长2小时
CACHE_DIR=cache        # 缓存目录
```

### Vercel 部署注意事项

#### vercel.json 配置
```json
{
  "version": 2,
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
  ]
}
```

#### 环境变量设置
在 Vercel 控制台中设置以下环境变量：
- `TTS_API_KEY`: 您的实际API密钥
- `HTTP_TIMEOUT`: `60`
- `RETRY_COUNT`: `2`
- `DEBUG`: `False`

### Docker 部署配置

#### Dockerfile 示例
```dockerfile
FROM python:3.12-slim

WORKDIR /home/engine/project
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "app:app"]
```

#### Docker 环境变量
```bash
-e TTS_API_KEY=your_api_key \
-e HTTP_TIMEOUT=60 \
-e RETRY_COUNT=2 \
-e DEBUG=False \
```

## 故障排查

### 1. 使用诊断端点

首先运行诊断端点确定问题范围：

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://your-domain.com/v1/audio/diagnose
```

### 2. 常见问题和解决方案

#### 问题1: DNS解析失败
**症状**: `dns_resolution: {status: "failed"}`
**解决方案**:
```bash
# 检查DNS配置
nslookup bot.n.cn

# 如果DNS有问题，配置hosts文件
echo "1.2.3.4 bot.n.cn" >> /etc/hosts
```

#### 问题2: SSL证书验证失败
**症状**: `ssl_certificate: {status: "failed"}`
**解决方案**:
```bash
# 开发环境可以临时禁用SSL验证
echo "SSL_VERIFY=false" >> .env

# 生产环境应该修复证书问题
# 联系网络管理员或证书提供商
```

#### 问题3: API认证失败
**症状**: `error_code: "110023"`
**解决方案**:
```bash
# 检查API密钥配置
echo $TTS_API_KEY

# 验证API密钥是否正确
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:5001/health
```

#### 问题4: 代理配置问题
**症状**: `basic_connectivity: {status: "failed"}`
**解决方案**:
```bash
# 如果需要代理，设置正确的代理地址
echo "PROXY_URL=http://your-proxy:8080" >> .env

# 测试代理连通性
curl --proxy $PROXY_URL https://bot.n.cn
```

### 3. 日志分析

#### 启用详细日志
```bash
export LOG_LEVEL=DEBUG
```

#### 查看实时日志
```bash
# 应用日志
tail -f logs/app.log

# 或者在控制台查看
python3 app.py
```

#### 关键日志信息
```bash
# 正常启动日志
2025-12-15 04:53:41 - INFO - TTS引擎配置: timeout=60s, retry=2, proxy=False, ssl_verify=True
2025-12-15 04:53:41 - INFO - 从缓存成功加载 14 个声音模型

# 正常TTS请求日志
2025-12-15 04:53:41 - INFO - 开始生成音频 - 模型: DeepSeek, 文本长度: 10 (尝试 1/3)
2025-12-15 04:53:41 - INFO - 音频生成成功 - 数据大小: 171102 字节; 校验: 有效的MP3文件(包含同步帧)

# 错误日志示例
2025-12-15 04:53:41 - ERROR - HTTP POST请求失败 (尝试 1) - HTTP错误: 500 - Internal Server Error
2025-12-15 04:53:41 - ERROR - API返回错误响应: {"code":"110023","message":"认证失败"}
```

## 监控和维护

### 1. 健康检查监控

定期检查服务健康状态：

```bash
# 健康检查脚本
curl -s http://your-domain.com/health | jq '.status'

# 如果返回 "ok" 表示正常
# 如果返回 "warning" 表示服务可用但有问题
# 如果返回 "error" 表示服务不可用
```

### 2. 性能监控

监控关键指标：
- API 响应时间
- 成功率/错误率
- 缓存命中率
- 并发请求数

### 3. 缓存管理

```bash
# 清理过期缓存
find cache/ -name "*.json" -mtime +1 -delete

# 手动刷新缓存
curl -X POST -H "Authorization: Bearer YOUR_API_KEY" \
     http://your-domain.com/v1/models
```

## 测试验证

### 1. 本地测试

```bash
# 启动服务
python3 app.py

# 运行诊断测试
python3 test_diagnosis.py
```

### 2. 生产环境测试

```bash
# 测试健康状态
curl http://your-domain.com/health

# 测试诊断端点
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://your-domain.com/v1/audio/diagnose

# 测试模型列表
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://your-domain.com/v1/models

# 测试TTS功能
curl -X POST \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"DeepSeek","input":"测试文本"}' \
     http://your-domain.com/v1/audio/speech \
     --output test_output.mp3
```

## 最佳实践

### 1. 安全配置
- 生产环境设置 `DEBUG=False`
- 使用强密码作为 API 密钥
- 定期轮换 API 密钥
- 启用 SSL 证书验证

### 2. 性能优化
- 根据网络情况调整 `HTTP_TIMEOUT`
- 合理设置缓存时长
- 监控内存使用情况
- 使用缓存减少网络请求

### 3. 监控告警
- 设置健康检查告警
- 监控错误率和响应时间
- 记录关键错误信息
- 建立日志分析机制

## 支持和故障排除

如果按照本指南操作后仍有问题，请：

1. 运行诊断端点获取详细信息
2. 检查相关日志文件
3. 确认网络连通性
4. 验证 API 密钥和配置
5. 联系技术支持团队

---

**版本**: v1.0  
**更新时间**: 2025-12-15  
**兼容性**: Python 3.12+, Flask 2.3+