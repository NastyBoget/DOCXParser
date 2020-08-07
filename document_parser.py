import zipfile
from bs4 import BeautifulSoup
import os
import sys
from styles_extractor import StylesExtractor
from numbering_extractor import NumberingExtractor
from data_structures import Paragraph


class DOCXParser:

    def __init__(self,
                 file: str):
        """
        parses the .docx document
        holds the text and metadata for each paragraph and raw in the document
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
        parses document into paragraphs and raws, extracts text for each raw and paragraph and it's metadata
        """

        body = self.document_bs.body
        if not body:
            return

        paragraphs = body.find_all('w:p')
        for paragraph in paragraphs:
            # TODO text may be without w:t
            if not paragraph.t:
                continue

            self.paragraph_list.append(Paragraph(paragraph, self.styles_extractor, self.numbering_extractor))

    def get_lines(self):
        """
        :return: list of document's lines
        """
        lines = []
        for paragraph in self.paragraph_list:
            line_text = ""
            for raw in paragraph.raws:
                line_text += raw.text
            lines.append(line_text)
        return lines

    def get_lines_with_meta(self):
        """
        :return: list of dictionaries for each paragraph
        [{"text": "", "properties": [[start, end, {"indent", "size", "bold", "italic", "underlined"}], ...] }, ...]
        start, end - character's positions begin with 0, end isn't included
        indent = {"firstLine", "hanging", "start", "left"}
        """
        lines_with_meta = []
        for paragraph in self.paragraph_list:
            lines_with_meta.append(paragraph.get_info())
        return lines_with_meta


if __name__ == "__main__":
    choice = input()
    if choice == "test":
        filenames = os.listdir('examples/docx/docx')[200:300]
    else:
        filenames = [choice]
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
                    for raw_info in line['properties']:
                        print('start={} end={} properties={}'.format(raw_info[0], raw_info[1], raw_info[2]), file=file)
                if choice == 'test':
                    print(f"\r{i} objects are processed...", end='', flush=True)
            except ValueError as err:
                print("ValueError: ", err)
                print(filename)
            except KeyError as err:
                print("KeyError: ", err)
                print(filename)
            except zipfile.BadZipFile:
                pass

# TODO docx/docx/doc_000651.docx, docx/docx/doc_000578.docx буквы вместо цифр
# TODO Домен.docx начало списка считается жирным, но оно нежирное
