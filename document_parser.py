import zipfile
from bs4 import BeautifulSoup
from styles_extractor import StylesExtractor


class DocumentParser:

    # TODO more complex structure extraction

    def __init__(self, file):
        # file - name of the docx file
        # TODO check ending with .docx
        document = zipfile.ZipFile('examples/' + file)
        self.document_bs = BeautifulSoup(document.read('word/document.xml'), 'xml')
        self.styles_extractor = StylesExtractor(BeautifulSoup(document.read('word/styles.xml'), 'xml'))
        self.data = []
        self.default_p_info = self.styles_extractor.parse(None)  # default style
        self.default_p_info['text'] = ''
        self.cur_p_info = self.default_p_info.copy()

    def parse(self):
        # returns the list of dictionaries for each paragraph
        # [{size, indent, bold, italic, underlined, text}, ...]

        body = self.document_bs.body
        if not body:
            return self.data

        for paragraph in body:

            if paragraph.pStyle:
                self.cur_p_info = self.styles_extractor.parse(paragraph.pStyle['w:val'])
                self.cur_p_info['text'] = ''
            else:
                self.cur_p_info = self.default_p_info.copy()

            # size
            if paragraph.sz:
                try:
                    self.cur_p_info['size'] = paragraph.sz['w:val']
                except KeyError:
                    pass
            self.cur_p_info['size'] = int(self.cur_p_info['size'])
            # indent
            # TODO different attributes for indent
            # TODO more accurate with previous paragraphs
            indent = paragraph.ind
            if indent:
                try:
                    self.cur_p_info['indent'] = int(indent['w:firstLine'])
                except KeyError:
                    try:
                        self.cur_p_info['indent'] = int(indent['w:left'])
                    except KeyError:
                        pass

            # bold
            # tag b in styles without value means '1'
            # tag b in pPr without value means '1'
            # TODO different values the same attribute in the same paragraph
            if paragraph.pPr:
                self.set_tag_value(paragraph.pPr.b, 'bold')

            # italic
            if paragraph.pPr:
                self.set_tag_value(paragraph.pPr.i, 'italic')

            # underlined
            if paragraph.u:
                try:
                    self.cur_p_info['underlined'] = paragraph.u['w:val']
                except KeyError:
                    pass

            raw_list = paragraph.find_all('w:r')
            for raw in raw_list:
                # text
                t = raw.t
                if t:
                    if t.text:
                        if not self.cur_p_info['text']:
                            self.cur_p_info['text'] = t.text
                        else:
                            self.cur_p_info['text'] += t.text

            self.data.append(self.cur_p_info.copy())

        return self.data

    def set_tag_value(self, tag, tag_name):
        # TODO more accurate with previous paragraphs
        if tag:
            try:
                self.cur_p_info[tag_name] = tag['w:val']
            except KeyError:
                self.cur_p_info[tag_name] = '1'


if __name__ == "__main__":
    filename = input()
    p = DocumentParser(filename)
    lines_info = p.parse()
    for line in lines_info:
        print(line)
