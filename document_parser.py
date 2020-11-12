import zipfile
from bs4 import BeautifulSoup
import os
import sys
import time
from typing import List
from styles_extractor import StylesExtractor
from numbering_extractor import NumberingExtractor
from data_structures import Paragraph, ParagraphInfo


class DOCXParser:

    def __init__(self,
                 file: str):
        """
        parses the .docx document
        holds the text and metadata for each paragraph and run in the document
        :param file: name of the .docx file
        """
        if not file.endswith('.docx'):
            raise ValueError('it is not .docx file')
        document = zipfile.ZipFile(file)
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
        self.footers, self.headers = [], []
        for i in range(1, 4):
            try:
                self.footers.append(BeautifulSoup(document.read(f'word/footer{i}.xml'), 'xml'))
            except KeyError:
                pass
            try:
                self.headers.append(BeautifulSoup(document.read(f'word/header{i}.xml'), 'xml'))
            except KeyError:
                pass
        try:
            self.footnotes = BeautifulSoup(document.read(f'word/footnotes.xml'), 'xml')
        except KeyError:
            self.footnotes = None
        try:
            self.endnotes = BeautifulSoup(document.read(f'word/endnotes.xml'), 'xml')
        except KeyError:
            self.endnotes = None
        # the list of paragraph with their properties
        self.paragraph_list = []
        self.parse()

    def parse(self):
        """
        parses document into paragraphs and runs, extracts text for each run and paragraph and it's metadata
        """
        if not self.document_bs:
            return None
        for header in self.headers:
            header_paragraphs = header.find_all('w:p')
            for paragraph in header_paragraphs:
                self.paragraph_list.append(Paragraph(paragraph,
                                                     self.styles_extractor, None))
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
                continue

            self.paragraph_list.append(Paragraph(paragraph, self.styles_extractor, self.numbering_extractor))
        if self.footnotes:
            footnotes_paragraphs = self.footnotes.find_all('w:p')
            for paragraph in footnotes_paragraphs:
                self.paragraph_list.append(Paragraph(paragraph,
                                                     self.styles_extractor, None))
        if self.endnotes:
            endnotes_paragraphs = self.endnotes.find_all('w:p')
            for paragraph in endnotes_paragraphs:
                self.paragraph_list.append(Paragraph(paragraph,
                                                     self.styles_extractor, None))
        for footer in self.footers:
            footer_paragraphs = footer.find_all('w:p')
            for paragraph in footer_paragraphs:
                self.paragraph_list.append(Paragraph(paragraph,
                                                     self.styles_extractor, None))

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
        "type": ""("paragraph" ,"list_item", "raw_text"), "level": (1,1) or None (hierarchy_level),
        "indent": {"firstLine", "hanging", "start", "left"}, "alignment": "" ("left", "right", "center", "both"),
        "annotations": [[start, end, size], [start, end, "bold"], [start, end, "italic"],
        [start, end, "underlined"], ...] } ]
        start, end - character's positions begin with 0, end isn't included
        """
        lines_with_meta = []
        for paragraph in self.paragraph_list:
            paragraph_properties = ParagraphInfo(paragraph)
            line_with_meta = paragraph_properties.get_info()
            if line_with_meta['text']:
                lines_with_meta.append(line_with_meta)
        return lines_with_meta


if __name__ == "__main__":
    choice = input()
    if choice == "test":
        filenames = os.listdir('examples/docx/docx')[:100]
    else:
        filenames = [choice]
    global_start = time.time()
    start = time.time()
    i = 0
    with open("results.txt", "w") as write_file:
        for filename in filenames:
            try:
                i += 1
                if choice == "test":
                    parser = DOCXParser('examples/docx/docx/' + filename)
                else:
                    parser = DOCXParser('examples/' + choice)
                lines_info = parser.get_lines_with_meta()
                if choice != "test":
                    file = sys.stdout
                else:
                    print("==================", file=write_file)
                    print(filename, file=write_file)
                    print("==================", file=write_file)
                    file = write_file
                for line in lines_info:
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
# footers_headers/footer_header_example_1.docx
