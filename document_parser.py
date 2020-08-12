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
        self.document_bs = BeautifulSoup(document.read('word/document.xml'), 'xml')
        self.styles_extractor = StylesExtractor(BeautifulSoup(document.read('word/styles.xml'), 'xml'))
        try:
            self.numbering_extractor = NumberingExtractor(BeautifulSoup(document.read('word/numbering.xml'), 'xml'),
                                                          self.styles_extractor)
            self.styles_extractor.numbering_extractor = self.numbering_extractor
        except KeyError:
            self.numbering_extractor = None
        # the list of paragraph with their properties
        self.paragraph_list = []
        self.parse()

    def parse(self):
        """
        parses document into paragraphs and runs, extracts text for each run and paragraph and it's metadata
        """

        body = self.document_bs.body
        if not body:
            return
        for paragraph in body:
            if paragraph.name == 'tbl':
                continue
            # TODO text may be without w:t
            if not paragraph.t:
                continue

            self.paragraph_list.append(Paragraph(paragraph, self.styles_extractor, self.numbering_extractor))

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
        [{"text": "", "type": ""("paragraph" ,"list_item", "raw_text"), "level": (1,1) (hierarchy_level),
        "properties": [[start, end, {"indent", "size", "alignment", "bold", "italic", "underlined"}], ...] }, ...]
        start, end - character's positions begin with 0, end isn't included
        indent = {"firstLine", "hanging", "start", "left"}
        """
        lines_with_meta = []
        for paragraph in self.paragraph_list:
            paragraph_properties = ParagraphInfo(paragraph)
            lines_with_meta.append(paragraph_properties.get_info())
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
                    for run_info in line['properties']:
                        print('start={} end={} type={} level={} properties={}'.format(run_info[0],
                                                                                      run_info[1],
                                                                                      line['type'],
                                                                                      line['level'],
                                                                                      run_info[2]), file=file)
                if choice == 'test':
                    print(f"\r{i} objects are processed...", end='', flush=True)
                if i % 100 == 0:
                    end = time.time()
                    print(end - start)
                    start = end
            except ValueError as err:
                pass
            except KeyError as err:
                print("KeyError: ", err)
                print(filename)
            except zipfile.BadZipFile:
                pass
    end = time.time()
    print(end - global_start)

# TODO docx/docx/doc_000651.docx, docx/docx/doc_000578.docx буквы вместо цифр
