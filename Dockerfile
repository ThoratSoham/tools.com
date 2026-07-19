# Use a slim Python base and add ffmpeg, which both yt-dlp and Whisper need.
FROM python:3.11-slim

# Install ffmpeg system dependency
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching on rebuilds)
COPY requirements.txt .
# openai-whisper's legacy setup.py needs pkg_resources, which recent
# setuptools versions no longer bundle by default. A plain global install
# of an older setuptools isn't enough — pip builds some packages in an
# *isolated* temp environment that fetches its own setuptools regardless.
# PIP_CONSTRAINT forces that pin to apply inside isolated builds too.
RUN pip install --no-cache-dir --upgrade pip "setuptools<81" wheel
RUN echo "setuptools<81" > /tmp/constraints.txt
ENV PIP_CONSTRAINT=/tmp/constraints.txt
ENV PIP_BUILD_CONSTRAINT=/tmp/constraints.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Pre-download the Whisper model at build time so the first real request
# isn't slow — remove this line if you'd rather download on first use.
RUN python -c "import whisper; whisper.load_model('base')"

EXPOSE 8080

# Use gunicorn instead of Flask's dev server for production.
# --timeout 300: transcription can take a while, don't kill long requests.
# --workers 1: Whisper holds the model in memory; more workers = more RAM,
#              multiply accordingly if you upgrade your hosting plan.
# Shell form so $PORT (set by Railway/Render/etc.) is respected; falls
# back to 8080 for local `docker run`. Wrapped in explicit sh -c with JSON
# array syntax so Docker forwards OS signals (e.g. Ctrl+C) correctly.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 300 app:app"]