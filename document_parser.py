import zipfile
from bs4 import BeautifulSoup
import os
import sys
import time
from typing import List
from styles_extractor import StylesExtractor
from numbering_extractor import NumberingExtractor
from data_structures.paragraph import Paragraph
from data_structures.paragraph_info import ParagraphInfo


class DOCXParser:

    def __init__(self):
        self.document_bs = None
        self.styles_extractor = None
        self.numbering_extractor = None
        # the list of paragraph with their properties
        self.paragraph_list = []
        self.paragraph_xml_list = []

    def can_parse(self,
                  filename: str) -> bool:
        """
        checks if DOCXParser can parse file with filename path
        :param filename: path to the file for checking
        """
        return filename.endswith(".docx")

    def parse(self,
              filename: str) -> None:
        """
        parses document into paragraphs and runs, extracts text for each run and paragraph and it's metadata
        :param filename: name of the .docx file
        """
        if not self.can_parse(filename):
            raise ValueError('it is not .docx file')

        document = zipfile.ZipFile(filename)
        try:
            self.document_bs = BeautifulSoup(document.read('word/document.xml'), 'xml')
        except KeyError:
            try:
                self.document_bs = BeautifulSoup(document.read('word/document2.xml'), 'xml')
            except KeyError:
                return
        self.styles_extractor = StylesExtractor(BeautifulSoup(document.read('word/styles.xml'), 'xml'))
        try:
            self.numbering_extractor = NumberingExtractor(BeautifulSoup(document.read('word/numbering.xml'), 'xml'),
                                                          self.styles_extractor)
            self.styles_extractor.numbering_extractor = self.numbering_extractor
        except KeyError:
            self.numbering_extractor = None

        # the list of paragraph with their properties
        self.paragraph_list = []
        self.paragraph_xml_list = []

        if not self.document_bs:
            return

        body = self.document_bs.body
        if not body:
            return
        for paragraph in body:
            if paragraph.name == 'tbl':
                continue
            if paragraph.name != 'p':
                child_paragraph_list = paragraph.find_all('w:p')
                for child_paragraph in child_paragraph_list:
                    self.paragraph_list.append(Paragraph(child_paragraph,
                                                         self.styles_extractor, self.numbering_extractor))
                    self.paragraph_xml_list.append(child_paragraph)
                continue

            self.paragraph_list.append(Paragraph(paragraph, self.styles_extractor, self.numbering_extractor))
            self.paragraph_xml_list.append(paragraph)

    def get_lines(self) -> List[str]:
        """
        :return: list of document's lines
        """
        lines = []
        for paragraph in self.paragraph_list:
            line_text = ""
            for run in paragraph.runs:
                line_text += run.text
            lines.append(line_text)
        return lines

    def get_lines_with_meta(self) -> List[dict]:
        """
        :return: list of dictionaries for each paragraph
        [{"text": "",
        "uid": "line unique identifier",
        "type": ""("paragraph" ,"list_item", "raw_text"), "level": (1,1) or None (hierarchy_level),
        "annotations": [("size", start, end, size), ("bold", start, end, True), ...] } ]
        start, end - character's positions begin with 0, end isn't included
        """
        lines_with_meta = []
        for paragraph in self.paragraph_list:
            paragraph_properties = ParagraphInfo(paragraph)
            line_with_meta = paragraph_properties.get_info()
            if line_with_meta['text']:
                lines_with_meta.append(line_with_meta)
        return lines_with_meta

    @property
    def get_paragraph_xml_list(self) -> List[BeautifulSoup]:
        return self.paragraph_xml_list

    @property
    def get_document_bs(self) -> BeautifulSoup:
        return self.document_bs


if __name__ == "__main__":
    choice = input()
    if choice == "test":
        filenames = os.listdir('examples/test')
    else:
        filenames = [choice]
    global_start = time.time()
    start = time.time()
    parser = DOCXParser()
    i = 0
    with open("examples/test/results.txt", "w") as write_file:
        for filename in filenames:
            try:
                i += 1
                if choice == "test":
                    if parser.can_parse('examples/test' + filename):
                        parser.parse('examples/test' + filename)
                else:
                    if parser.can_parse('examples/' + choice):
                        parser.parse('examples/' + choice)
                lines_info = parser.get_lines_with_meta()
                if choice != "test":
                    file = sys.stdout
                else:
                    print("==================", file=write_file)
                    print(filename, file=write_file)
                    print("==================", file=write_file)
                    file = write_file
                for line in lines_info:
                    print(line)
                    print(line['text'], file=file)
                    print(line['annotations'], file=file)
                    print(line['level'], file=file)

                if choice == 'test':
                    print(f"\r{i} objects are processed...", end='', flush=True)
                if i % 100 == 0:
                    end = time.time()
                    print(end - start)
                    start = end
            except ValueError as err:
                print("ValueError: ", err)
                print(filename)
            except KeyError as err:
                print("KeyError: ", err)
                print(filename)
            except zipfile.BadZipFile:
                pass

# TODO docx/docx/doc_000651.docx, docx/docx/doc_000578.docx буквы вместо цифр
