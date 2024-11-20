from flask import Flask, render_template, request, redirect, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
import tempfile
import shutil
import subprocess

app = Flask(__name__)
app.config['UPLOAD_DIRECTORY'] = 'uploads/'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    # files is an array
        # file = request.files['folder-input[]']
        # if file:
        #     file.save(os.path.join(
        #         app.config['UPLOAD_DIRECTORY'], 
        #         secure_filename(file.filename)))

    if 'folder-input' not in request.files:
        return "No folder input in the request", 400

    files = request.files.getlist('folder-input')

        # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save uploaded files to temp directory
        for file in files:
            if file.filename:
                file.save(os.path.join(temp_dir, secure_filename(file.filename)))
        
        # Create output directory for processed files
        processed_dir = tempfile.mkdtemp()
        
        try:
            # Run EE_Data_process2.py
            subprocess.run(['python', 'EE_Data_process2.py', 
                          '--input', temp_dir,
                          '--output', processed_dir], 
                         check=True)
            
            # Run EE_Find_duplicates.py on the processed files
            final_dir = tempfile.mkdtemp()
            subprocess.run(['python', 'EE_Find_duplicates.py',
                          '--input', processed_dir,
                          '--output', final_dir],
                         check=True)
            
            # Create zip file from final directory
            zip_path = os.path.join(app.config['UPLOAD_DIRECTORY'], 'processed_files.zip')
            shutil.make_archive(zip_path[:-4], 'zip', final_dir)
            
            # Cleanup temporary processed directory
            shutil.rmtree(processed_dir)
            shutil.rmtree(final_dir)
            
            # Return the zip file to user
            return send_file(zip_path, as_attachment=True)
            
        except subprocess.CalledProcessError as e:
            return f"Error processing files: {str(e)}", 500
        except Exception as e:
            return f"Unexpected error: {str(e)}", 500
            
        return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)