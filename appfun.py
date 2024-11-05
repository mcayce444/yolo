from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import EE_Data_process2
import EE_Find_duplicates

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', message=None)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'folder-input' not in request.files:
        return "No folder input in the request", 400
    files = request.files.getlist('folder-input')


@app.route('/return-folder')
def return_folder():
    return_file_path = r"casetesting.xlsx"
    #return send_file(excel_file_path, as_attachment=True, download_name="casetesting.xlsx")


if __name__ == '__main__':
    app.run(debug=True)