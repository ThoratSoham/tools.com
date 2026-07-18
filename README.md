# tools.com
# Link Collector — Video Transcript Extractor

A small Flask app that takes a YouTube or Instagram video link and returns a
plain-text transcript. YouTube uses its own captions when available;
Instagram (and any YouTube video without captions... not yet supported) uses
local speech-to-text via [OpenAI Whisper](https://github.com/openai/whisper).

## How it works

- **YouTube** — downloads only the caption file (`.vtt`), no video/audio, and
  converts it to clean plain text.
- **Instagram** — downloads audio only, transcribes it locally with Whisper,
  then deletes the audio file.

No files are kept after processing; everything happens in a temp folder that
gets cleaned up per request.

## Requirements

- Python 3.11 or 3.12 (Whisper's dependencies, especially PyTorch, may not
  have wheels available yet for very new Python versions like 3.13/3.14)
- [ffmpeg](https://ffmpeg.org/) installed and available on your system PATH
  — required by both `yt-dlp` (audio extraction) and Whisper (audio
  decoding)

### Windows users on a managed/corporate machine

If your organization uses **Device Guard / Windows Defender Application
Control**, native Windows ffmpeg builds may be blocked from running even
after installing them. If you hit an error like:

```
'ffmpeg.exe' was blocked by your organization's Device Guard policy.
```

the reliable fix is to run this project inside **WSL2 (Ubuntu)** instead of
native Windows — Device Guard policies typically don't extend into the WSL
Linux environment. See the WSL setup notes below.

## Setup

### 1. Install ffmpeg

**macOS**
```bash
brew install ffmpeg
```

**Linux / WSL2 (Ubuntu)**
```bash
sudo apt update
sudo apt install ffmpeg -y
```

**Windows (native)**
```powershell
winget install ffmpeg
```
Then close and reopen your terminal so PATH updates take effect.

Verify it worked:
```bash
ffmpeg -version
```

### 2. Set up a virtual environment

> **Important:** create and use a *separate* venv per OS/environment. A venv
> created inside WSL/Linux will not work from native Windows PowerShell, and
> vice versa — they contain OS-specific binaries and symlinks.

```bash
python3 -m venv .venv

# macOS/Linux/WSL
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\activate
```

### 3. Install Python dependencies

```bash
pip install flask yt-dlp webvtt-py openai-whisper
```

> **Watch out for this specific trap:** there is a PyPI package literally
> called `whisper` that is completely unrelated to OpenAI's speech-to-text
> library and will break on import. Always install `openai-whisper`, never
> `whisper` directly. If you've already installed the wrong one:
> ```bash
> pip uninstall whisper -y
> pip install openai-whisper
> ```

### 4. Run the app

```bash
python3 app.py
```

Wait for:
```
Running on http://127.0.0.1:5000
```

Then open **http://127.0.0.1:5000/** in your browser. WSL2 forwards
`localhost` automatically, so this works the same whether the server is
running natively on Windows/macOS/Linux or inside WSL.

> **Do not** open `index.html` directly as a file, or serve it separately
> with a tool like VS Code's Live Server. The frontend calls a relative
> `/process-link` endpoint that only exists on the Flask server itself —
> opening the HTML file on its own will not reach it.

## Project structure

```
.
├── app.py          # Flask backend: routing, yt-dlp, Whisper transcription
├── index.html       # Frontend UI, served by Flask at '/'
├── .gitignore
└── README.md
```

## Notes and known limitations

- **Instagram scraping is fragile.** Instagram aggressively rate-limits and
  blocks anonymous requests via `yt-dlp`. Many links, especially from
  private or heavily-viewed accounts, may fail even with everything set up
  correctly. Passing browser cookies to `yt-dlp` (`cookiesfrombrowser`)
  can improve reliability but is not currently wired in.
- **First run is slow.** Whisper downloads its model weights (~150MB for
  the `base` model) the first time it runs.
- **Playlists/channel URLs are rejected** by design — only single-video
  links are supported.
- This is a local development server (Flask's built-in dev server,
  `debug=False`, bound to `127.0.0.1` only). It is not configured for
  production or public network exposure.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `ERR_CONNECTION_REFUSED` on `127.0.0.1:5000` | Server isn't actually running — check the terminal for errors, or you're using Live Server instead of `python3 app.py` |
| "Server did not return JSON" in the UI | The browser reached something other than this Flask app (wrong port, Live Server, stray process already on port 5000) |
| `ffmpeg not found` | ffmpeg isn't installed or isn't on PATH — see Setup step 1 |
| `ffmpeg.exe was blocked by your organization's Device Guard policy` | Run the project inside WSL2 instead of native Windows |
| `ImportError` / `ctypes.CDLL` error on `import whisper` | You installed the wrong `whisper` package — install `openai-whisper` instead |
| Transcription works for YouTube but not Instagram | Usually Instagram blocking anonymous `yt-dlp` requests — not a bug in this code |