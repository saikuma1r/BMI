from flask import Flask, render_template, request, send_file
from gtts import gTTS
import fitz  # PyMuPDF
from pydub import AudioSegment
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = 'audio'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return '''
        <h1>PDF to Audio</h1>
        <form action="/convert" method="post" enctype="multipart/form-data">
            <input type="file" name="pdf_file" required>
            <input type="submit" value="Convert to Audio">
        </form>
    '''

@app.route('/convert', methods=['POST'])
def convert_pdf_to_audio():
    pdf = request.files['pdf_file']
    if not pdf.filename.endswith('.pdf'):
        return 'Please upload a valid PDF file.'

    pdf_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
    pdf.save(pdf_path)

    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    audio_files = []

    if num_pages <= 10:
        text = ""
        for page in doc:
            text += page.get_text()
        audio = gTTS(text)
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(AUDIO_FOLDER, audio_filename)
        audio.save(audio_path)
        return send_file(audio_path, as_attachment=True)

    # For larger PDFs, convert each page and combine
    combined_audio = AudioSegment.empty()
    for page in doc:
        page_text = page.get_text()
        if not page_text.strip():
            continue
        tts = gTTS(page_text)
        temp_audio_path = os.path.join(AUDIO_FOLDER, f"{uuid.uuid4()}.mp3")
        tts.save(temp_audio_path)
        segment = AudioSegment.from_mp3(temp_audio_path)
        combined_audio += segment
        os.remove(temp_audio_path)

    final_audio_filename = f"{uuid.uuid4()}_combined.mp3"
    final_audio_path = os.path.join(AUDIO_FOLDER, final_audio_filename)
    combined_audio.export(final_audio_path, format="mp3")

    return send_file(final_audio_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)