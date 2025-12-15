# nami-tts

An OpenAI-compatible TTS gateway with a provider/fallback framework.

## Features

- `POST /v1/audio/speech` (OpenAI-compatible)
- Multiple TTS providers (NanoAI, Google gTTS, Azure)
- Provider priority + automatic fallback
- Vercel-ready deployment

## Configuration

Copy `.env.example` to `.env` for local development.

Key variables:

- `SERVICE_API_KEY` (or legacy `TTS_API_KEY`)
- `DEFAULT_TTS_PROVIDER`
- `TTS_PROVIDER_PRIORITY`
- Provider credentials such as `AZURE_API_KEY` + `AZURE_REGION`

## Endpoints

- `GET /v1/providers`
- `GET /v1/models?provider=<name>`
- `POST /v1/audio/speech` (JSON body supports `provider`, `speed`, `language`, ...)
- `GET/POST /v1/config`
- `GET /health`
