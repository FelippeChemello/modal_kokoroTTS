# modal-kokoro

Text-to-Speech (TTS) service using the Kokoro model running on Modal, exposed via a FastAPI endpoint with API key authentication. Includes a local entrypoint that generates a `output.wav` sample.

## Overview

- FastAPI POST endpoint returning `audio/wav`.
- GPU-backed inference on Modal (`L40S`), falls back to CPU if unavailable.
- Simple API key check via `x-api-key` header.
- Local entrypoint to quickly test and write a `.wav` file.

## Prerequisites

- Python `>=3.10`
- Modal CLI and account (to run/deploy): `pip install modal`
- Access to a GPU in your Modal account (the app requests `gpu="L40S"`)

## Setup

1. Clone the repo and create your environment file:
   - Copy `.env.example` to `.env` and set values:
     - `API_KEY` — any long random string you will use to authorize requests.
     - `BASE_URL` — fill after deploy (optional; used by `api.rest`).

2. Sign in to Modal:
   - `modal setup` (or ensure your Modal credentials are configured).

3. Optional: The app references a Modal secret named `kokoro-secret`.
   - If you need to store credentials, create it in Modal and populate as needed.
   - The current code does not read values from this secret, but Modal expects it to exist when deploying.

## Run Locally (quick check)

The local entrypoint runs a sample TTS and writes `output.wav` in the repo root:

```
modal run app.py
```

You can adjust the sample text/voice in `app.py` under `main()`.

## Deploy the Web Endpoint

Deploy to Modal to get a public HTTPS endpoint:

```
modal deploy app.py
```

Copy the printed URL and set it as `BASE_URL` in your `.env` if you plan to use `api.rest`.

## API Usage

- Method: `POST`
- URL: your deployed `BASE_URL`
- Headers: `x-api-key: <your API_KEY>` and `Content-Type: application/json`
- Body:

```json
{
  "text": "Olá, este é um exemplo de síntese de fala usando Kokoro.",
  "voice": "pf_dora"
}
```

Example with `curl` (writes the result to `output.wav`):

```
curl -X POST "$BASE_URL" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"Olá, este é um exemplo de síntese de fala usando Kokoro.","voice":"pf_dora"}' \
  --output output.wav
```

Notes:
- The current pipeline is initialized with `lang_code="p"` (Portuguese). Voices should match that language.
- The request body only needs `text` and `voice`. Any `lang` field is currently ignored by the server.

## Using `api.rest`

An example REST client file is provided at `api.rest` and reads variables from `.env`. Update `.env` with your `API_KEY` and `BASE_URL` and execute the request with a compatible REST client.

## Voices

Kokoro provides multiple voices (e.g., `pf_dora`). Refer to Kokoro resources for the full list and choose a voice compatible with the configured language. You can change the language by editing `KPipeline(lang_code=...)` in `app.py` and using corresponding voices.

## Project Structure

- `app.py` — Modal app, FastAPI endpoint, and local entrypoint.
- `api.rest` — sample request for REST clients, uses `.env` values.
- `.env.example` — template for environment variables.
- `pyproject.toml` — project metadata.

## Troubleshooting

- GPU access: Ensure your Modal account/project has access to the requested GPU type (`L40S`). The app will fall back to CPU if CUDA is unavailable, but inference may be slower.
- Authorization: A missing or incorrect `x-api-key` returns `401 Unauthorized`.
- Outputs: Local runs write `output.wav` in the repo root; `.gitignore` excludes `.wav` files by default.

## Security

- Do not commit `.env`. The repo’s `.gitignore` already excludes it.
- Keep `API_KEY` secret and rotate it if exposed.
