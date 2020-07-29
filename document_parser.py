import zipfile
from bs4 import BeautifulSoup
import os
from styles_extractor import StylesExtractor
from numbering_extractor import NumberingExtractor
from properties_extractor import PropertiesExtractor


class DOCXParser:

    def __init__(self, file):
        # file - name of the docx file
        if not file.endswith('.docx'):
            raise ValueError("it is not .docx file")
        document = zipfile.ZipFile(file)
        self.document_bs = BeautifulSoup(document.read('word/document.xml'), 'xml')
        self.styles_extractor = StylesExtractor(BeautifulSoup(document.read('word/styles.xml'), 'xml'))
        try:
            self.numbering_extractor = NumberingExtractor(BeautifulSoup(document.read('word/numbering.xml'), 'xml'),
                                                          self.styles_extractor)
        except KeyError:
            self.numbering_extractor = None
        self.data = []  # the list of properties for all paragraphs
        self.empty_p_info = self.styles_extractor.parse(None)

    def parse(self):
        # returns the list of dictionaries for each paragraph
        # [{"text": "", "properties": [[start, end, {indent, size, bold, italic, underlined}], ...] }, ...]
        # start, end - character's positions begin with 0, end isn't included
        # indent = {firstLine, hanging, start, left}

        body = self.document_bs.body
        if not body:
            return self.data

        # hierarchy: properties in styles (+ numbering) -> direct properties (paragraph, character)
        # 1) documentDefault (styles.xml)
        # 2) tables (styles.xml)
        # 3) paragraphs styles (styles.xml)
        # 4) numbering styles (styles.xml, numbering.xml)
        # 5) characters styles (styles.xml)
        # 6) direct formatting (document.xml)
        for paragraph in body:

            # properties in styles
            if paragraph.pStyle:
                p_info = self.styles_extractor.parse(paragraph.pStyle['w:val'], "paragraph")
            else:
                # cur_p_info = {'size': 0, 'indent': {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0},
                # 'bold': '0', 'italic': '0', 'underlined': 'none'}
                p_info = self.empty_p_info

            # numbering properties
            if paragraph.numPr:
                num_pr = self.numbering_extractor.parse(paragraph.numPr)
            else:
                num_pr = None
            # num_pr = {"text": text of list element,
            # "pPr": {'size': 0, 'indent': {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0},
            # 'bold': '0', 'italic': '0', 'underlined': 'none'}, "rPr": None or
            # {'size': 0, 'bold': '0', 'italic': '0', 'underlined': 'none'}} for text in num_pr
            # TODO check this behavior
            if num_pr:
                for indent_type, value in num_pr["pPr"]['indent'].items():
                    if value != 0:
                        p_info['indent'][indent_type] = value

            # paragraph direct formatting
            # TODO more accurate with previous paragraphs
            if paragraph.pPr:
                pe = PropertiesExtractor(paragraph.pPr)
                pe.get_properties(p_info)

            item = {"text": "", "properties": []}
            prev_r_info = p_info.copy()
            # TODO check this behavior
            if num_pr:
                item["text"] += num_pr["text"]
                start, end = 0, len(item["text"])
                num_info = p_info.copy()
                if num_pr["rPr"]:
                    for r_property, value in num_pr["rPr"].items():
                        if r_property != 'size' or value:  # size value should not be 0
                            num_info[r_property] = value

                item["properties"].append([start, end, num_info.copy()])
                prev_r_info = num_info

            # character direct formatting
            raw_list = paragraph.find_all('w:r')
            for raw in raw_list:
                if not raw.t or not raw.t.text:
                    continue

                start, end = len(item['text']), len(item['text']) + len(raw.t.text)
                if not item['text']:
                    item['text'] = raw.t.text
                else:
                    item['text'] += raw.t.text

                r_info = p_info.copy()
                if raw.rPr:
                    pe = PropertiesExtractor(raw.rPr)
                    pe.get_properties(r_info)

                if prev_r_info == r_info and item['properties']:
                    item['properties'][-1][1] = end  # change the end of such properties
                else:
                    item['properties'].append([start, end, r_info.copy()])
                    prev_r_info = r_info

            print(item['text'])
            self.data.append(item.copy())
        return self.data


if __name__ == "__main__":
    choice = input()
    if choice == "test":
        filenames = os.listdir('examples/docx/docx')
    else:
        filenames = [choice]
    i = 0
    try:
        for filename in filenames:
            i += 1
            if choice == "test":
                parser = DOCXParser('examples/docx/docx/' + filename)
            else:
                parser = DOCXParser('examples/' + choice)
            lines_info = parser.parse()
            if choice != "test":
                for line in lines_info:
                    print(line['text'])
                    for raw_info in line['properties']:
                        print('start={} end={} properties={}'.format(raw_info[0], raw_info[1], raw_info[2]))
            if choice == 'test':
                print(f"\r{i} objects are processed...", end='', flush=True)
    except ValueError:
        pass
# Problems:
# 1) intend 0
# 2) example9.docx - error in numbering parse, \n in some paragraphs ???, bold='false'
# 3) example9.docx АИС «УЗЕЛ ИНФРАСТРУКТУРЫ ПРОСТРАНСТВЕННЫХ ДАННЫХ РОССИЙСКОЙ ФЕДЕРАЦИИ» italic???
# 4) rStyle
