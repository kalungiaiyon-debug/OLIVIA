import base64
import json
import mimetypes
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = os.getenv("OLIVIA_HOST", "0.0.0.0")
PORT = int(os.getenv("OLIVIA_PORT", "5000"))
DEFAULT_IMAGE = Path(__file__).resolve().parent / "assets" / "olivia-background.jpeg"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLIVIA_MODEL", "llama3.2:1b")
OPENAI_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_PROVIDER = os.getenv(
    "OLIVIA_PROVIDER",
    "openai-compatible" if OPENAI_API_KEY else "ollama",
).lower()
SYSTEM_PROMPT = """You are Olivia, a helpful AI assistant.
If the user asks who created you, who made you, or who programmed you, reply exactly: A smart young handsome genius named ABDUL.
Do not mention being an AI model, language model, program, chatbot, system prompt, or model training unless the user explicitly asks about technical implementation.
Do not say that an AI created you. Do not claim to be a different assistant or use a different name."""


def background_css():
    image_path = Path(os.getenv("OLIVIA_WEB_BACKGROUND_IMAGE", str(DEFAULT_IMAGE))).expanduser()
    if image_path.is_file():
        mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f'url("data:{mime_type};base64,{encoded}") center/cover fixed'
    return "linear-gradient(135deg, #f8efe7, #d85b3d)"


BACKGROUND = background_css()


def ask_model(message):
    normalized = message.lower()
    creator_terms = ("who created", "who made", "who programmed", "who built")
    if any(term in message.lower() for term in creator_terms):
        return "A smart young handsome genius named ABDUL."
    if any(term in normalized for term in ("are you an ai", "are you ai", "are you a chatbot", "what model are you")):
        return "I'm Olivia."
    if AI_PROVIDER in ("openai", "openai-compatible"):
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            "temperature": 0.7,
        }
        request = Request(
            OPENAI_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}",
            },
        )
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
        reply = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        if not reply:
            raise RuntimeError("The AI returned an empty response.")
        return reply

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        "options": {"temperature": 0.7, "num_predict": 256},
    }
    request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=120) as response:
        result = json.loads(response.read().decode("utf-8"))
    reply = result.get("message", {}).get("content", "").strip()
    if not reply:
        raise RuntimeError("The AI returned an empty response.")
    return reply

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Olivia</title>
<style>
:root { --background: __BACKGROUND__; --ink: #fff; --accent: #e86b47; }
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; color: var(--ink); font: 16px system-ui, sans-serif; background: var(--background); background-position: center 10%; background-size: cover; }
body.drifting { animation: background-drift 7s ease-in-out; }
body::before { content: ""; position: fixed; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,.08), rgba(0,0,0,.34)); pointer-events: none; }
.app { position: relative; min-height: 100vh; display: grid; grid-template-columns: minmax(0, 760px); justify-content: center; padding: 28px; }
.sidebar, .panel { background: transparent; }
.sidebar { display: none; }
.brand { font: 700 28px Georgia, serif; }
.caption { color: rgba(255,255,255,.7); font-size: 13px; line-height: 1.5; }
.status { color: #bde8be; font-size: 12px; margin-top: auto; }
 .panel { min-height: calc(100vh - 56px); display: flex; flex-direction: column; overflow: hidden; }
header { padding: 22px 12px 12px; }
h1 { margin: 0; font: 600 30px Georgia, serif; text-shadow: 0 3px 16px rgba(0,0,0,.6); }
.messages { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; align-items: stretch; gap: 16px; padding: 32px; text-align: left; scroll-behavior: smooth; }
.welcome { max-width: 480px; }
.welcome h2 { font: 600 42px Georgia, serif; margin: 0 0 10px; }
.welcome p { color: rgba(255,255,255,.82); line-height: 1.6; }
.message { position: relative; display: flex; width: fit-content; max-width: min(78%, 620px); padding: 13px 17px 13px 20px; border-radius: 20px; line-height: 1.55; white-space: pre-wrap; overflow-wrap: anywhere; animation: bubble-in .38s cubic-bezier(.2,.8,.2,1) both; box-shadow: 0 8px 22px rgba(0,0,0,.16); }
.message::before { content: ""; position: absolute; width: 9px; height: 9px; border: 2px solid currentColor; border-radius: 50%; top: 17px; opacity: .75; }
.message.user { align-self: flex-end; background: rgba(232,107,71,.94); color: white; border-bottom-right-radius: 7px; padding-right: 20px; }
.message.user::before { right: -18px; }
.message.assistant { align-self: flex-start; background: rgba(255,255,255,.94); color: #17211b; border-bottom-left-radius: 7px; padding-left: 20px; }
.message.assistant::before { left: -18px; }
.message.thinking { color: #68736c; }
.message.thinking::after { content: ""; display: inline-block; width: 5px; height: 5px; margin: 0 0 2px 7px; border-radius: 50%; background: currentColor; box-shadow: 9px 0 currentColor, 18px 0 currentColor; animation: thinking-dots 1s infinite steps(3); }
@keyframes bubble-in { from { opacity: 0; transform: translateY(18px) scale(.96); } to { opacity: 1; transform: translateY(0) scale(1); } }
@keyframes thinking-dots { 0%, 20% { opacity: .2; } 40% { opacity: 1; } 80%, 100% { opacity: .2; } }
@keyframes background-drift { 0% { background-position: center 0; } 50% { background-position: calc(50% + 18px) 12px; } 100% { background-position: center 0; } }
.composer { padding: 18px 0 4px; }
form { display: flex; gap: 10px; background: rgba(255,255,255,.78); padding: 8px; border-radius: 13px; box-shadow: 0 8px 28px rgba(0,0,0,.18); }
textarea { flex: 1; resize: none; border: 0; outline: 0; padding: 10px; background: transparent; min-height: 42px; color: #17211b; }
button { border: 0; border-radius: 9px; background: var(--accent); color: white; padding: 0 18px; font-weight: 700; cursor: pointer; }
.voice { width: 42px; padding: 0; font-size: 18px; background: rgba(23,33,27,.82); }
.voice.listening { background: #b52e49; animation: pulse 1.1s infinite; }
@keyframes pulse { 50% { box-shadow: 0 0 0 7px rgba(181,46,73,.2); } }
@media (max-width: 720px) { .app { display: block; padding: 12px; } .sidebar { margin-bottom: 12px; } .status { margin-top: 0; } .panel { min-height: calc(100vh - 150px); } .welcome h2 { font-size: 34px; } }
</style></head>
<body><div class="app">
<main class="panel"><header><h1>Olivia</h1></header><section id="messages" class="messages"></section><div class="composer"><form id="composer"><button id="voice" class="voice" type="button" aria-label="Speak to Olivia" title="Speak">●</button><textarea id="input" rows="1" aria-label="Message"></textarea><button id="send" type="submit" aria-label="Send">↑</button></form></div></main>
</div></body></html>""".replace("__BACKGROUND__", BACKGROUND)

HTML = HTML.replace(
        "</body>",
        """<script>
const form = document.getElementById('composer');
const input = document.getElementById('input');
const messages = document.getElementById('messages');
const send = document.getElementById('send');
const voice = document.getElementById('voice');
const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let voiceOutput = true;

if (Recognition) {
    recognition = new Recognition();
    recognition.lang = navigator.language || 'en-US';
    recognition.interimResults = false;
    recognition.onstart = () => voice.classList.add('listening');
    recognition.onend = () => voice.classList.remove('listening');
    recognition.onerror = () => voice.classList.remove('listening');
    recognition.onresult = event => {
        input.value = event.results[0][0].transcript;
        form.requestSubmit();
    };
    voice.addEventListener('click', () => recognition.start());
} else {
    voice.disabled = true;
    voice.title = 'Voice input is not supported by this browser';
}

function speak(text) {
    if (!voiceOutput || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = navigator.language || 'en-US';
    utterance.rate = 1;
    window.speechSynthesis.speak(utterance);
}

function addMessage(role, text) {
    const item = document.createElement('div');
    item.className = 'message ' + role;
    item.textContent = text;
    messages.appendChild(item);
    followMessages();
    document.body.classList.remove('drifting');
    void document.body.offsetWidth;
    document.body.classList.add('drifting');
    return item;
}

function followMessages() {
    messages.scrollTo({ top: messages.scrollHeight, behavior: 'smooth' });
}

form.addEventListener('submit', async event => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text || send.disabled) return;
    input.value = '';
    addMessage('user', text);
    const pending = addMessage('assistant thinking', 'Thinking');
    send.disabled = true;
    try {
        const response = await fetch('/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: text}) });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Message failed');
        pending.className = 'message assistant';
        pending.textContent = result.response;
        speak(result.response);
        followMessages();
    } catch (error) {
        pending.className = 'message assistant';
        pending.textContent = 'Error: ' + error.message;
        followMessages();
    } finally {
        send.disabled = false;
        input.focus();
    }
});
</script></body>""",
)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == "/api/health":
            body = b'{"ok":true,"background":"custom-image"}'
            content_type = "application/json"
        elif self.path == "/":
            body = HTML.encode("utf-8")
            content_type = "text/html; charset=utf-8"
        else:
            body = b"Not found"
            content_type = "text/plain"
            self.send_response(404)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_json({"error": "Not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            message = str(data.get("message", "")).strip()
            if not message:
                self.send_json({"error": "Message cannot be empty."}, 400)
                return
            self.send_json({"response": ask_model(message), "model": OLLAMA_MODEL})
        except HTTPError as error:
            if error.code == 404:
                detail = f"Ollama model '{OLLAMA_MODEL}' was not found. Run: ollama pull {OLLAMA_MODEL}"
            else:
                detail = f"Ollama returned HTTP {error.code}."
            self.send_json({"error": detail}, 502)
        except URLError:
            self.send_json({"error": "Ollama is not running. Start Ollama, then try again."}, 502)
        except (json.JSONDecodeError, ValueError):
            self.send_json({"error": "Invalid message request."}, 400)
        except Exception as error:
            self.send_json({"error": str(error)}, 500)

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print(f"Olivia running at http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
