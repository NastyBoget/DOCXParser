from document_parser import DOCXParser
import json
import docx
import re
import numpy as np
import xgboost as xgb
from sklearn.metrics import f1_score

TRAIN_PATH = 'examples/train_examples/labeled.json'
TEST_PATH = 'examples/test_examples/labeled.json'


alignment2number = {
    "left": 0,
    "right": 1,
    "center": 2,
    "both": 3
}

type2number = {
    "paragraph": 1,
    "list_item": 2,
    "raw_text": 3
}


def process_doc(path):
    document = docx.Document(path)
    item = {"name": path, "paragraphs": []}
    for paragraph in document.paragraphs:
        if not paragraph.text.strip():
            continue
        p = {"text": paragraph.text}
        item["paragraphs"].append(p)
    return [item]


def prepare_data(data, labels=False):
    clear_data = []
    for item in data:
        new_item = {"name": item["name"], "paragraphs": []}
        for p in item['paragraphs']:
            p_info = {}
            if p['text'].strip():
                p_info['text'] = p['text'].strip()
                if labels:
                    p_info['type'] = int(p['type'])
                    p_info['level'] = int(p['level'])
                new_item["paragraphs"].append(p_info)
        if new_item["paragraphs"]:
            clear_data.append(new_item)

    data_without_labels = []
    if labels:
        labels_list = []

    for item in clear_data:
        new_item = {"name": item["name"], "paragraphs": []}
        for p in item['paragraphs']:
            new_item["paragraphs"].append(p["text"])
            if labels:
                labels_list.append((p["type"], p["level"]))
        data_without_labels.append(new_item)
    if labels:
        labels_list = [y * 10 + x for x, y in labels_list]
        return data_without_labels, labels_list
    else:
        return data_without_labels


def find_paragraph(paragraph_list, text):
    for p in paragraph_list:
        # TODO correct comparison
        #         print(f"real text={' '.join(p['text'].split())}")
        #         print(f"text={' '.join(text.split())}")
        #         print("===========")
        if " ".join(p["text"].split()).find(" ".join(text.split())) != -1:
            result = p.copy()
            paragraph_list.remove(p)
            return result
    return None


def extract_annotations(annotations):
    result = {"indent": [0, 0, 0, 0], "alignment": 0, "size": 0, "bold": 0, "italic": 0, "underlined": 0}
    if not annotations:
        return result
    for start, end, annotation in annotations:
        if annotation.startswith("indent"):
            d = json.loads(re.sub("'", '"', annotation[7:]))
            result["indent"] = [d["left"], d["start"], d["hanging"], d["firstLine"]]
        elif annotation.startswith("alignment"):
            result["alignment"] = alignment2number[annotation[10:]]
        elif annotation.startswith("size"):
            result["size"] = int(annotation[5:])
        else:
            for item in ["bold", "italic", "underlined"]:
                if annotation.startswith(item):
                    result[item] = 1
                    break
    return result


def extract_doc_features(docs_info):
    """
    docs_info = list of {"name", "paragraphs": ["text of 1 line", "text of 2 line"]}
    returns list of features for each paragraph
    """
    features = []
    for doc_info in docs_info:
        path = doc_info["name"]
        parser = DOCXParser(path)
        lines_info = parser.get_lines_with_meta()
        for p in doc_info["paragraphs"]:
            p_features = []
            p_info = find_paragraph(lines_info, p)
            if p_info:
                p_features.append(type2number[p_info["type"]])
            else:
                p_features.append(3)
                p_info = {"text": "", "annotations": None}
            p_annotations = extract_annotations(p_info["annotations"])
            p_features += p_annotations["indent"]
            p_features += [p_annotations["alignment"], p_annotations["size"],
                           p_annotations["bold"], p_annotations["italic"], p_annotations["underlined"]]
            p_features.append(len(p_info["text"].split()))

            if p_info["text"].split():
                first_word = p_info["text"].split()[0]
            else:
                first_word = ""
            p_features.append(len(first_word))
            p_features.append(len(re.findall(r"\d+", first_word)))
            features.append(p_features)
    return np.array(features)


class LinesClassifier:
    def __init__(self):
        self.clf = xgb.XGBClassifier()

    def fit(self):
        with open('examples/train_examples/labeled.json', "r") as f:
            data = json.load(f)
        data, labels = prepare_data(data, labels=True)
        features = extract_doc_features(data)
        self.clf.fit(features, labels)

    def test(self, path='examples/test_examples/labeled.json'):
        with open(path, "r") as f:
            data = json.load(f)
        data, labels = prepare_data(data, labels=True)
        features = extract_doc_features(data)
        return f1_score(labels, self.clf.predict(features), average='macro')

    def predict(self, data):
        data = prepare_data(data)
        features = extract_doc_features(data)
        return self.clf.predict(features)


if __name__ == "__main__":
    clf = LinesClassifier()
    clf.fit()
    print(clf.test())
