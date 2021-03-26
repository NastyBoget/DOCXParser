import os
import zipfile
from bs4 import BeautifulSoup

from docx_parser.document_parser import DOCXParser


def get_xml(doc_name: str, xml_name: str = 'word/document.xml') -> str:
    document = zipfile.ZipFile(doc_name)
    try:
        bs = BeautifulSoup(document.read(xml_name), 'xml')
    except KeyError:
        return ""
    return bs.prettify()


if __name__ == "__main__":
    doc_name = "2.docx"
    # word/styles.xml
    # word/numbering.xml
    with open("document.xml", "w") as f:
        print(get_xml(doc_name), file=f)

    with open("numbering.xml", "w") as f:
        print(get_xml(doc_name, "word/numbering.xml"), file=f)

    doc_name = os.path.abspath(doc_name)
    docx_parser = DOCXParser()
    docx_parser.parse(doc_name)
    lines = docx_parser.get_lines_with_meta()
    for line in lines:
        print(line["text"])
