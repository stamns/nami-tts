# nami-tts

一个 OpenAI 兼容的 TTS 网关服务，内置多提供商框架与自动降级。

## 功能

- `POST /v1/audio/speech`（OpenAI 兼容）
- 多 TTS 提供商（NanoAI、Google gTTS、Azure）
- 提供商优先级与自动降级
- 可直接部署到 Vercel

## 配置

本地开发时将 `.env.example` 复制为 `.env`。

关键环境变量：

- `SERVICE_API_KEY`（或兼容旧变量 `TTS_API_KEY`）
- `DEFAULT_TTS_PROVIDER`
- `TTS_PROVIDER_PRIORITY`
- 各提供商密钥（例如 Azure 需要 `AZURE_API_KEY` + `AZURE_REGION`）

## API

- `GET /v1/providers`
- `GET /v1/models?provider=<name>`
- `POST /v1/audio/speech`（支持 `provider`、`speed`、`language` 等参数）
- `GET/POST /v1/config`
- `GET /health`
