from flask import Flask, request, jsonify, send_file, render_template
import os
from werkzeug.utils import secure_filename
#from flask_wtf import FlaskForm
#from wtforms import FileField, SubmitField
import subprocess
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'key'
app.config['UPLOAD_FOLDER'] = 'static/files'

@app.route('/')
def index():
    return render_template('index.html', message=None)

@app.route('/upload-folder', methods=['POST'])
def upload_folder():
    # Ensure the request contains files
    if 'folder' not in request.files:
        return jsonify({'error': 'No folder part in the request'}), 400

    # Get the folder from the request
    folder = request.files.getlist('folder')
    if not folder:
        return jsonify({'error': 'No folder provided'}), 400

    # Create a secure folder name and save files
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_folder')
    os.makedirs(folder_path, exist_ok=True)

    for file in folder:
        filename = secure_filename(file.filename)
        file.save(os.path.join(folder_path, filename))

    return jsonify({'message': 'Folder uploaded successfully', 'folder_path': folder_path}), 200

@app.route('/process-folder', methods=['POST'])
def process_folder():
    # Ensure the 'folder_path' parameter is in the request
    if 'folder_path' not in request.json:
        return jsonify({'error': 'folder_path is required'}), 400

    # Get the folder path from the request
    folder_path = request.json['folder_path']

    # Validate if the folder exists
    if not os.path.isdir(folder_path):
        return jsonify({'error': 'Provided folder path does not exist'}), 400

    # Create temporary folder to store the output of ee_duplicate.py
    result_folder = os.path.join(folder_path, 'result_folder')
    os.makedirs(result_folder, exist_ok=True)

    # Execute ee_duplicate.py with the folder_path as an argument
    try:
        # Running ee_duplicate.py and saving output to result_folder
        subprocess.run(['python', 'EE_Data_process2.py', folder_path, result_folder], check=True)
        subprocess.run(['python', 'EE_Find_duplicates.py', result_folder, result_folder], check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Error occurred while running ee_duplicate.py: {str(e)}'}), 500

    # Create a zip file to return the updated folder
    zip_filename = os.path.join(folder_path, 'result_folder.zip')
    shutil.make_archive(zip_filename.replace('.zip', ''), 'zip', result_folder)

    return send_file(zip_filename, as_attachment=True), 200

if __name__ == '__main__':
    app.run(debug=True)
