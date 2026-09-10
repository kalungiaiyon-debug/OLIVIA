# Olivia deployment

Olivia is a small Python web app. The included Render configuration runs it as a 24/7 web service.

## Deploy on Render

1. Push this folder to a GitHub repository.
2. In Render, choose **New > Blueprint** and select the repository.
3. Render reads `render.yaml` and creates the web service.
4. Set `OPENAI_API_KEY` in the Render dashboard. Do not commit the key.
5. Deploy and open the generated `https://...onrender.com` URL.

The cloud deployment uses an OpenAI-compatible provider because the local Ollama process at `127.0.0.1:11434` is not available inside a normal cloud web service. You can use another compatible endpoint by changing `OPENAI_BASE_URL`.

## Background image

The selected background is bundled at `assets/olivia-background.jpeg`, so the same image is used locally and on Render. You can override it with `OLIVIA_WEB_BACKGROUND_IMAGE` when needed.

## Local run

```powershell
$env:OLIVIA_PROVIDER = "ollama"
$env:OLIVIA_MODEL = "llama3.2:1b"
python olivia_bridge.py
```
