import os
from typing import List, Dict
from flask import Flask, request
import tempfile
from werkzeug.datastructures import FileStorage
import json
from classifier import process_doc, LinesClassifier

static_path = os.path.join(os.path.dirname(__file__))
app = Flask(__name__, static_url_path=static_path)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


def doc2json(path: str) -> List[Dict]:
    data = process_doc(path)
    clf = LinesClassifier()
    clf.fit()
    y = clf.predict(data)
    res = []
    for line, label in zip(data[0]["paragraphs"], y):
        res.append({"label": str(label), "content": line["text"]})
    return res


def _get_file(request) -> FileStorage:
    return request.files['file']


def process_file_and_send_response(path):
    json_string = doc2json(path)

    response = app.response_class(
        response=json.dumps(obj=json_string, ensure_ascii=False, indent=2),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        uploaded_file = _get_file(request)
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_path = os.path.join(tmpdirname, uploaded_file.filename.split("/")[-1])
            uploaded_file.save(tmp_path)
            return process_file_and_send_response(tmp_path)

    return app.send_static_file("main_page.html")


@app.route('/example_docx', methods=['GET'])
def send_pdf():
    return app.send_static_file("example.docx")


@app.route("/example_json", methods=['GET'])
def process_pdf():
    return process_file_and_send_response("static/example.docx")


if __name__ == "__main__":
    # app.secret_key = b'_5#y2L_h4Q8z\n\xec]/'
    app.run(host='0.0.0.0', port=8889)
