import os
import yt_dlp
import webvtt
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)


def get_youtube_transcript(video_url, output_dir=None):
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_subs")

    os.makedirs(output_dir, exist_ok=True)
    output_template = os.path.join(output_dir, '%(id)s.%(ext)s')

    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': 'vtt',
        'subtitleslangs': ['en'],
        'outtmpl': output_template,
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=True)
            video_id = info['id']
            vtt_filename = os.path.join(output_dir, f"{video_id}.en.vtt")

            if not os.path.exists(vtt_filename):
                return {"error": "Transcript not found or unavailable in this language."}

            vtt = webvtt.read(vtt_filename)
            lines = []

            for caption in vtt:
                for line in caption.text.strip().splitlines():
                    lines.append(line)

            clean_lines = []
            previous_line = None
            for line in lines:
                if line == previous_line:
                    continue
                clean_lines.append(line)
                previous_line = line

            os.remove(vtt_filename)
            full_transcript = " ".join(clean_lines)
            return {"title": info.get('title'), "transcript": full_transcript}

        except Exception as exc:
            return {"error": f"An error occurred: {exc}"}


@app.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')


@app.route('/process-link', methods=['POST'])
def process_link():
    data = request.get_json(silent=True) or request.form or {}
    link = (data.get('link') or '').strip()

    if not link:
        return jsonify({"success": False, "error": "Please provide a valid link."}), 400

    if not link.startswith(('http://', 'https://')):
        link = f"https://{link}"

    result = get_youtube_transcript(link)

    if 'error' in result:
        return jsonify({"success": False, "error": result['error']}), 400

    return jsonify({"success": True, "title": result.get('title'), "transcript": result.get('transcript')})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)