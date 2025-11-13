from flask import Flask, request, render_template_string, send_from_directory, abort
import os
import subprocess
import uuid
import time

app = Flask(__name__)
DOWNLOAD_DIR = 'downloads'  # Folder for temporary video files
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Clean up old files (optional: run periodically)
def cleanup_downloads():
    for file in os.listdir(DOWNLOAD_DIR):
        path = os.path.join(DOWNLOAD_DIR, file)
        if os.path.isfile(path) and time.time() - os.path.getmtime(path) > 3600:  # Delete after 1 hour
            os.remove(path)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        if not url or 'youtube.com' not in url:
            return 'Invalid YouTube URL!', 400

        # Generate unique filename
        filename = f"{uuid.uuid4().hex}.mp4"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        try:
            # Run yt-dlp to download (best video+audio, merge to mp4)
            subprocess.check_call([
                'yt-dlp',
                '-f', 'bv*+ba/b',  # Best video + best audio, merged
                '-o', filepath,
                '--no-playlist',  # Single video only
                url
            ])
            return render_template_string("""
                <h1>Download Ready!</h1>
                <a href="/download/{{ filename }}" download>Click to Download Video</a>
            """, filename=filename)
        except subprocess.CalledProcessError:
            abort(500, description="Download failed—check the URL or try again.")

    # Cleanup (optional)
    cleanup_downloads()

    # Form HTML
    return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>YouTube Downloader</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 2rem auto; }
                input, button { font-size: 1rem; padding: .5rem; margin: .5rem 0; width: 100%; }
            </style>
        </head>
        <body>
            <h1>Paste YouTube Link</h1>
            <form method="post">
                <input name="url" type="text" placeholder="https://www.youtube.com/watch?v=...">
                <button type="submit">Download</button>
            </form>
        </body>
        </html>
    '''

@app.route('/download/<filename>')
def download(filename):
    try:
        return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)
    finally:
        # Optional: Delete after download to save space
        os.remove(os.path.join(DOWNLOAD_DIR, filename))

if __name__ == '__main__':
    app.run(debug=True)  # For production, use a WSGI server like gunicorn
