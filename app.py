from flask import Flask, request, send_file
from gtts import gTTS
import fitz  # PyMuPDF
import os
import uuid
import zipfile

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

    if num_pages <= 10:
        text = "".join([page.get_text() for page in doc])
        audio = gTTS(text)
        audio_path = os.path.join(AUDIO_FOLDER, f"{uuid.uuid4()}.mp3")
        audio.save(audio_path)
        return send_file(audio_path, as_attachment=True)

    # For large PDFs: one audio per page, zipped
    zip_filename = os.path.join(AUDIO_FOLDER, f"{uuid.uuid4()}.zip")
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for i, page in enumerate(doc):
            text = page.get_text().strip()
            if not text:
                continue
            audio = gTTS(text)
        
            # Make a unique filename for each page
            audio_filename = f"page_{i + 1}_{uuid.uuid4().hex[:6]}.mp3"
            page_audio_path = os.path.join(AUDIO_FOLDER, audio_filename)
        
            audio.save(page_audio_path)
            zipf.write(page_audio_path, audio_filename)  # Write to zip using filename only
            os.remove(page_audio_path)  # Clean up individual file after adding to zip
            
if __name__ == '__main__':
    app.run(debug=True)
