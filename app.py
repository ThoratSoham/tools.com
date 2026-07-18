import os
import glob
import logging
from urllib.parse import urlparse

import yt_dlp
import webvtt
import whisper
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load a lightweight Whisper model into memory (runs locally)
# 'tiny' or 'base' are very fast and perfect for quick web backend tasks
model = whisper.load_model("base")

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com"}


def extract_from_youtube(video_url, output_dir):
    """Fast, download-free transcript route for YouTube."""
    output_template = os.path.join(output_dir, '%(id)s.%(ext)s')
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': 'vtt',
        'subtitleslangs': ['en', 'en-orig', 'en-US'],
        'outtmpl': output_template,
        'quiet': True,
        'noplaylist': True,
    }

    vtt_filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)

        if 'entries' in info:
            raise ValueError("Playlists/channels are not supported. Please provide a single video link.")

        video_id = info['id']

        # Caption filenames vary: en.vtt, en-orig.vtt, en-US.vtt, etc.
        candidates = glob.glob(os.path.join(output_dir, f"{video_id}.en*.vtt"))
        if not candidates:
            raise FileNotFoundError("No English captions available for this YouTube video.")

        vtt_filename = candidates[0]

        lines = [
            line
            for caption in webvtt.read(vtt_filename)
            for line in caption.text.strip().splitlines()
        ]

        # Simple sequential deduplication
        clean_lines = []
        for line in lines:
            line = line.strip()
            if line and (not clean_lines or line != clean_lines[-1]):
                clean_lines.append(line)

        return " ".join(clean_lines)

    finally:
        if vtt_filename and os.path.exists(vtt_filename):
            os.remove(vtt_filename)


def extract_from_instagram(video_url, output_dir):
    """Audio download + AI speech-to-text transcription route for Instagram."""
    output_template = os.path.join(output_dir, '%(id)s.%(ext)s')
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    audio_filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)

        audio_filename = os.path.join(output_dir, f"{info['id']}.mp3")

        if not os.path.exists(audio_filename):
            raise FileNotFoundError("Audio download failed.")

        result = model.transcribe(audio_filename)
        return result["text"].strip()

    finally:
        if audio_filename and os.path.exists(audio_filename):
            os.remove(audio_filename)


def get_platform(url):
    """Determine platform by parsing the actual hostname, not substring matching."""
    try:
        host = urlparse(url).netloc.lower()
        # Strip port if present
        host = host.split(':')[0]
    except Exception:
        return None

    if host in YOUTUBE_HOSTS:
        return "youtube"
    if host in INSTAGRAM_HOSTS:
        return "instagram"
    return None


def process_video_link(url):
    """Unified entry point for both YouTube and Instagram links."""
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend_temp")
    os.makedirs(temp_dir, exist_ok=True)

    platform = get_platform(url)

    try:
        if platform == "youtube":
            transcript = extract_from_youtube(url, temp_dir)
        elif platform == "instagram":
            transcript = extract_from_instagram(url, temp_dir)
        else:
            return {"success": False, "error": "Unsupported platform. Please provide a YouTube or Instagram link."}

        return {"success": True, "transcript": transcript}

    except Exception as exc:
        # Log full detail server-side, return a safe message to the client
        logger.exception("Failed to process video link: %s", url)
        return {"success": False, "error": f"Could not process this link: {exc}"}


@app.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')


@app.route('/process-link', methods=['POST'])
def process_link():
    try:
        data = request.get_json(silent=True) or request.form or {}
    except Exception:
        data = {}

    link = (data.get('link') or '').strip() if isinstance(data, dict) else ''

    if not link:
        return jsonify({"success": False, "error": "Please provide a valid link."}), 400

    result = process_video_link(link)
    if not result.get("success"):
        return jsonify(result), 400

    return jsonify(result)


# --- Global error handlers -------------------------------------------------
# Flask's default error pages are HTML, which breaks frontend code that
# expects JSON (response.json() throws "unexpected response"). These
# handlers guarantee every response from this server is valid JSON.

@app.errorhandler(404)
def handle_404(e):
    return jsonify({"success": False, "error": "Not found."}), 404


@app.errorhandler(405)
def handle_405(e):
    return jsonify({"success": False, "error": "Method not allowed."}), 405


@app.errorhandler(413)
def handle_413(e):
    return jsonify({"success": False, "error": "Request too large."}), 413


@app.errorhandler(500)
def handle_500(e):
    logger.exception("Unhandled server error")
    return jsonify({"success": False, "error": "Internal server error. Please try again."}), 500


@app.errorhandler(Exception)
def handle_uncaught(e):
    # Catch-all safety net: any exception not handled above still comes
    # back as JSON instead of Flask's default HTML traceback/error page.
    logger.exception("Uncaught exception")
    return jsonify({"success": False, "error": "Something went wrong on the server."}), 500


if __name__ == '__main__':
    # For local development only. Bind to localhost, not 0.0.0.0, and keep
    # debug mode off unless you are the only one who can reach this machine.
    # If you need LAN/external access, run behind gunicorn/uwsgi with debug=False.
    app.run(debug=False, host='127.0.0.1', port=5000)