# 常见问题 (FAQ) - NanoAI TTS

[![返回 README](https://img.shields.io/badge/返回-README--CN-blue?style=flat-square)](./README-CN.md)
[![部署指南](https://img.shields.io/badge/部署-DEPLOYMENT--CN-green?style=flat-square)](./DEPLOYMENT-CN.md)
[![使用示例](https://img.shields.io/badge/示例-EXAMPLES--CN-purple?style=flat-square)](./EXAMPLES-CN.md)

本文档收集了用户在使用 NanoAI TTS 过程中最常遇到的问题和解决方案。

## 📋 目录

- [安装和环境相关](#安装和环境相关)
- [API 密钥和认证](#api-密钥和认证)
- [功能和使用](#功能和使用)
- [性能和优化](#性能和优化)
- [部署问题](#部署问题)
- [错误排查](#错误排查)
- [收费和配额](#收费和配额)
- [安全和隐私](#安全和隐私)

## 🔧 安装和环境相关

### Q1: 安装依赖时报错，怎么办？

**常见错误**:
```
ERROR: Could not install packages due to an EnvironmentError
```

**解决方案**:

1. 升级 pip
```bash
pip install --upgrade pip
```

2. 使用国内镜像（如果网络慢）
```bash
pip install -r requirements.txt -i https://pypi.tsinghua.edu.cn/simple
```

3. 逐个安装依赖以确定问题包
```bash
pip install Flask==2.3.3
pip install Flask-CORS==4.0.0
# ... 逐个安装
```

4. 检查 Python 版本
```bash
python3 --version
# 需要 Python 3.8+
```

### Q2: 虚拟环境无法激活？

**Linux/macOS**:
```bash
# 错误的方式
cd venv/bin
source activate

# 正确的方式
source venv/bin/activate
```

**Windows**:
```bash
# 正确的方式
venv\Scripts\activate

# 如果不行，尝试
python -m venv venv
```

### Q3: 应用无法启动，提示 "Port already in use"？

**解决方案**:

```bash
# 查找占用端口的进程
# Linux/macOS
lsof -i :5001

# Windows
netstat -ano | findstr :5001

# 杀死进程（替换 PID）
# Linux/macOS
kill -9 <PID>

# Windows
taskkill /PID <PID> /F

# 或使用不同的端口
export PORT=5002
python3 app.py
```

### Q4: 如何在后台运行应用？

```bash
# Linux/macOS - 使用 nohup
nohup python3 app.py > app.log 2>&1 &

# 或使用 screen
screen -S tts
python3 app.py
# Ctrl+A D 分离

# 重新连接
screen -r tts

# Windows - 使用 pythonw
pythonw app.py
```

## 🔐 API 密钥和认证

### Q5: 如何获取 NanoAI API Key？

**步骤**:

1. 访问 https://bot.n.cn
2. 注册账户或登录
3. 进入设置/API 管理区域
4. 创建新的 API Key
5. 复制 Key 到 `.env` 文件

```env
TTS_API_KEY=sk-your-key-here
```

### Q6: API Key 不小心泄露了，怎么办？

**立即行动**:

1. 访问服务提供商网站删除该 Key
2. 生成新的 Key
3. 更新应用配置
4. 重启应用

```bash
# 检查是否有泄露的 key 在代码中
grep -r "sk-" . --exclude-dir=.git --exclude-dir=venv
```

### Q7: 为什么认证失败？提示 "110023" 错误？

这是 NanoAI API 的认证失败错误，通常原因：

1. **API Key 错误**
   ```bash
   # 验证 Key 是否正确
   echo $TTS_API_KEY
   ```

2. **时间偏差** (最常见)
   - 应用会自动同步时间
   - 检查系统时间是否正确
   ```bash
   date
   # 与网络时间对比
   ```

3. **网络问题**
   - 检查是否能访问 API 服务器
   ```bash
   curl -I https://bot.n.cn
   ```

4. **API Key 过期或被禁用**
   - 重新生成 API Key

### Q8: 支持多个 API 吗？如何配置？

**是的**，支持多个 TTS 提供商。在 `.env` 中配置：

```env
# NanoAI（必需）
TTS_API_KEY=sk-nanoai-key

# Google TTS（可选）
GOOGLE_API_KEY=google-key
GOOGLE_PROJECT_ID=project-id

# 百度 TTS（可选）
BAIDU_APP_ID=app-id
BAIDU_API_KEY=api-key
BAIDU_SECRET_KEY=secret-key

# 指定优先级
TTS_PROVIDER_PRIORITY=nanoai,google,baidu
```

## 🎯 功能和使用

### Q9: 支持的最大文本长度是多少？

**理论上无限，实际限制**:

- **单次请求**: 建议不超过 10,000 字
- **超长文本**: 系统会自动分段处理
- **API 限制**: 根据提供商限制

**最佳实践**:
```python
# 自动分段处理
max_length = 5000
text_chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]

for chunk in text_chunks:
    response = requests.post(...)
```

### Q10: 如何选择合适的模型和语言？

**可用的语言代码**:

| 代码 | 语言 |
|------|------|
| zh-CN | 简体中文 |
| zh-TW | 繁体中文 |
| en-US | 美国英语 |
| en-GB | 英国英语 |
| ja-JP | 日语 |
| ko-KR | 韩语 |
| es-ES | 西班牙语 |
| fr-FR | 法语 |
| de-DE | 德语 |
| ru-RU | 俄语 |

**查询可用模型**:

```bash
# 获取所有模型
curl http://localhost:5001/v1/models | jq

# 按提供商过滤
curl "http://localhost:5001/v1/models?provider=nanoai" | jq
```

### Q11: 生成的音频质量怎样？能调整吗？

**影响质量的因素**:

1. **模型选择**: 不同模型音质不同
2. **速度 (speed)**: 0.5-2.0，推荐 1.0
3. **音调 (pitch)**: 0.5-2.0，推荐 1.0
4. **音量 (volume)**: 0.0-1.0，推荐 1.0

**优化建议**:

```python
# 高质量配置
response = requests.post('...', json={
    'model': 'DeepSeek',      # 高质量模型
    'speed': 0.95,            # 略慢，更清晰
    'pitch': 1.0,             # 正常音调
    'volume': 0.9,            # 略低，避免爆音
})
```

### Q12: 支持哪些输出格式？

**支持的格式**:

- **MP3** (推荐) - 文件小，兼容性好
- **WAV** - 无损格式，文件较大
- **OGG** - 中等压缩，好兼容性

```python
response = requests.post('...', json={
    'format': 'mp3',  # 或 'wav', 'ogg'
})
```

### Q13: 可以用于商业用途吗？

**取决于**:

1. **您的 API Key 的条款**: 检查 TTS 提供商的服务协议
2. **使用规模**: 免费额度通常限制在小规模使用
3. **归属**: 某些服务可能要求标注来源

**建议**:
- 阅读 API 提供商的服务条款
- 联系提供商确认商业使用权限
- 考虑付费版本以获得完全商业权限

## ⚡ 性能和优化

### Q14: 为什么生成速度慢？

**可能的原因和解决方案**:

1. **网络延迟**
   ```bash
   # 测试网络延迟
   curl -w "@curl-format.txt" -o /dev/null -s https://bot.n.cn
   ```

2. **API 响应慢**
   - 增加超时时间
   ```env
   HTTP_TIMEOUT=120
   ```

3. **文本太长**
   - 减少单次文本长度
   - 或者批量使用并发处理

4. **缓存未启用**
   ```env
   CACHE_ENABLED=true
   CACHE_DURATION=7200
   ```

5. **服务器负载高**
   - 错开高峰时段
   - 使用 CDN 加速

### Q15: 如何加快生成速度？

**优化策略**:

```python
# 1. 使用缓存（相同文本快 100 倍）
CACHE_ENABLED=true

# 2. 使用快速的 API 提供商
'provider': 'nanoai'  # 最快

# 3. 并发处理
import concurrent.futures

def generate_many(texts):
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(generate_one, text) for text in texts]
        return [f.result() for f in futures]

# 4. 减少文本长度
max_length = 500

# 5. 启用压缩
response.headers['Content-Encoding'] = 'gzip'
```

### Q16: 缓存如何工作？能禁用吗？

**缓存工作原理**:

1. 计算输入的哈希值
2. 查找缓存目录中的匹配文件
3. 如果找到且未过期，返回缓存
4. 否则调用 API，保存结果到缓存

**配置缓存**:

```env
# 启用/禁用缓存
CACHE_ENABLED=true

# 缓存过期时间（秒）
CACHE_DURATION=7200

# 缓存目录
CACHE_DIR=cache

# 最大缓存大小（MB）
MAX_CACHE_SIZE=500
```

**清理缓存**:

```bash
# 清空所有缓存
rm -rf cache/*

# 只删除过期缓存
find cache/ -type f -mtime +1 -delete

# 删除特定文件
rm cache/specific_hash.mp3
```

### Q17: 如何监控应用性能？

**启用详细日志**:

```env
LOG_LEVEL=DEBUG
```

**使用诊断端点**:

```bash
curl http://localhost:5001/v1/audio/diagnose | jq
```

**监控指标**:

```bash
# 应用运行时间
uptime

# 内存使用
top -p $(pgrep -f app.py)

# 请求统计
tail -100 app.log | grep "INFO" | wc -l
```

## 🚀 部署问题

### Q18: Vercel 部署失败，怎么办？

**常见问题和解决**:

1. **环境变量未设置**
   - 在 Vercel 控制台检查环境变量
   - 确保 `TTS_API_KEY` 已设置

2. **构建失败**
   - 检查 `requirements.txt` 是否完整
   - 查看构建日志

3. **运行时错误**
   - 查看部署日志
   - 测试 API 端点
   ```bash
   curl https://your-app.vercel.app/health
   ```

4. **超时问题**
   - Vercel 限制函数执行时间为 12 秒
   - 使用缓存减少重复调用

**完整部署检查**:

```bash
# 1. 本地测试通过
python3 app.py

# 2. 检查依赖
pip list | grep -E "Flask|python-dotenv"

# 3. 测试 API
curl http://localhost:5001/health

# 4. 推送到 GitHub
git push origin main

# 5. Vercel 自动部署
# 检查部署状态和日志
```

### Q19: Docker 部署无法连接 API？

**常见问题**:

1. **网络隔离**
   ```bash
   # 确保容器能访问外网
   docker run --network host ...
   ```

2. **环境变量未传递**
   ```bash
   docker run -e TTS_API_KEY=your-key ...
   ```

3. **DNS 解析问题**
   ```bash
   # 指定 DNS
   docker run --dns 8.8.8.8 ...
   ```

4. **代理配置**
   ```bash
   docker run -e PROXY_URL=http://proxy:8080 ...
   ```

**完整的 Docker 运行命令**:

```bash
docker run -it --rm \
  -p 5001:5001 \
  -e TTS_API_KEY=sk-your-key \
  -e HTTP_TIMEOUT=60 \
  -e DEBUG=False \
  --name nanoai-tts \
  nanoai-tts:latest
```

### Q20: 在企业网络中如何部署？

**通常需要的配置**:

1. **代理设置**
   ```env
   PROXY_URL=http://proxy.company.com:8080
   ```

2. **SSL 证书**
   ```env
   SSL_VERIFY=true
   # 或使用自定义证书
   ```

3. **防火墙规则**
   ```bash
   # 允许出站 HTTPS
   # 允许与 TTS API 的连接
   # 通常是 bot.n.cn:443
   ```

4. **网络测试**
   ```bash
   # 测试连通性
   curl -x http://proxy:8080 https://bot.n.cn
   
   # 查看诊断信息
   curl http://localhost:5001/v1/audio/diagnose
   ```

## 🐛 错误排查

### Q21: 遇到错误信息，如何排查？

**系统的排查方法**:

1. **收集错误信息**
   ```bash
   # 查看完整错误日志
   tail -100 app.log
   ```

2. **运行诊断**
   ```bash
   curl http://localhost:5001/v1/audio/diagnose | jq
   ```

3. **测试 API 连接**
   ```bash
   # 直接测试 API
   curl https://bot.n.cn
   ```

4. **检查配置**
   ```bash
   # 验证环境变量
   env | grep TTS
   env | grep API
   ```

5. **查看日志**
   ```bash
   # 启用调试日志
   export LOG_LEVEL=DEBUG
   python3 app.py
   ```

### Q22: 如何获取详细的错误信息？

**启用调试模式**:

```env
DEBUG=True
LOG_LEVEL=DEBUG
```

**查看详细诊断**:

```bash
curl -H "Authorization: Bearer YOUR_KEY" \
  http://localhost:5001/v1/audio/diagnose | jq
```

**分析错误日志**:

```bash
# 搜索错误
grep "ERROR" app.log

# 搜索特定错误代码
grep "110023" app.log

# 查看上下文
grep -B5 -A5 "ERROR" app.log
```

### Q23: "503 Service Unavailable" 错误？

**可能原因**:

1. **API 服务不可用**
   - 检查提供商状态页面
   - 等待服务恢复

2. **应用崩溃**
   ```bash
   # 重启应用
   python3 app.py
   ```

3. **端口被占用**
   ```bash
   # 更改端口或释放当前端口
   export PORT=5002
   python3 app.py
   ```

4. **内存不足**
   ```bash
   # 查看内存使用
   free -h
   ```

### Q24: "timeout" 错误？

**解决方案**:

1. **增加超时时间**
   ```env
   HTTP_TIMEOUT=120
   ```

2. **检查网络**
   ```bash
   ping bot.n.cn
   ```

3. **减少文本长度**
   - 长文本需要更多时间

4. **检查 API 状态**
   - 服务器可能过载

## 💰 收费和配额

### Q25: 如何了解 API 的收费情况？

**NanoAI 免费额度**:

- **3000 万字符/月** 免费额度
- 超过后按量付费

**查询用量**:

1. 登录 https://bot.n.cn
2. 进入账户或控制面板
3. 查看使用统计

**成本计算示例**:

```
- 1 分钟语音 ≈ 500-1000 字符
- 1 小时有声书 ≈ 30,000-50,000 字符
- 月免费额度 ≈ 可生成 600-1000 小时音频
```

### Q26: 如何减少 API 调用成本？

**优化策略**:

1. **启用缓存** (最有效)
   ```env
   CACHE_ENABLED=true
   CACHE_DURATION=7200
   ```

2. **批量处理**
   - 一次请求多个句子，而不是逐个请求

3. **重用 API Key**
   - 在团队内共享（注意安全）

4. **选择合适的提供商**
   - NanoAI 提供最多的免费额度

## 🔒 安全和隐私

### Q27: API Key 的安全如何保证？

**最佳实践**:

1. **不要在代码中硬编码**
   ```python
   # ❌ 不要这样做
   api_key = "sk-your-key-here"
   
   # ✅ 正确做法
   api_key = os.getenv('TTS_API_KEY')
   ```

2. **使用环境变量**
   ```bash
   export TTS_API_KEY=sk-your-key
   ```

3. **在 .gitignore 中排除 .env**
   ```bash
   echo ".env" >> .gitignore
   ```

4. **定期轮换 Key**
   - 每个月生成新 Key
   - 删除旧 Key

5. **监控使用**
   - 定期检查 API 使用日志
   - 设置告警

### Q28: 用户数据会被保存吗？

**数据处理**:

- **输入文本**: 仅用于生成音频，不持久化保存
- **生成的音频**: 缓存在本地目录，可手动删除
- **日志**: 记录在应用日志中，不包含敏感信息

**隐私设置**:

```env
# 禁用日志（不推荐）
LOG_LEVEL=ERROR

# 清理缓存
rm -rf cache/*

# 定期清理日志
find . -name "*.log" -mtime +30 -delete
```

### Q29: 如何在 GDPR 合规的情况下使用？

**合规建议**:

1. **数据处理协议**
   - 与 TTS 提供商签订 DPA
   - 确保符合数据保护法规

2. **用户同意**
   - 获取用户同意处理其文本
   - 公示隐私政策

3. **数据保留**
   ```env
   # 自动清理过期数据
   CACHE_DURATION=86400  # 1 天
   ```

4. **加密传输**
   ```env
   SSL_VERIFY=true
   ```

5. **访问控制**
   ```env
   REQUIRE_AUTH=true
   ```

### Q30: 如何防止滥用？

**安全措施**:

1. **API 密钥管理**
   - 定期轮换
   - 权限最小化

2. **请求限流**
   ```env
   RATE_LIMIT_ENABLED=true
   RATE_LIMIT_PER_MINUTE=60
   ```

3. **监控异常使用**
   ```bash
   # 检查异常流量
   grep "POST /v1/audio/speech" app.log | wc -l
   ```

4. **黑名单和白名单**
   - 限制特定 IP 或用户

---

## 📞 还有其他问题？

如果你的问题不在这里，请：

1. 检查 [README](./README-CN.md)
2. 查看 [部署指南](./DEPLOYMENT-CN.md)
3. 查看 [使用示例](./EXAMPLES-CN.md)
4. 在 GitHub 提交 Issue: https://github.com/stamns/nami-tts/issues
5. 加入讨论区: https://github.com/stamns/nami-tts/discussions

---

**最后更新**: 2025年12月15日  
**版本**: 1.0  
**贡献者**: TTS 社区
