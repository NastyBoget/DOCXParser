import zipfile
from bs4 import BeautifulSoup
from styles_extractor import StylesExtractor


class DocumentParser:

    def __init__(self, file):
        # file - name of the docx file
        # TODO check ending with .docx
        document = zipfile.ZipFile('examples/' + file)
        self.document_bs = BeautifulSoup(document.read('word/document.xml'), 'xml')
        self.styles_extractor = StylesExtractor(BeautifulSoup(document.read('word/styles.xml'), 'xml'))
        self.data = []
        self.default_p_info = self.styles_extractor.parse(None)  # default style
        self.default_p_info['text'] = ''
        self.cur_p_info = self.default_p_info
        self.prev_p_info = None

    def parse(self):
        # returns the list of dictionaries for each paragraph
        # [{size, indent, bold, italic, underlined, text}, ...]
        # assumptions:
        # tag b in styles without value means '1'
        # tag b in pPr without value means '1'
        body = self.document_bs.body
        if not body:
            return self.data

        for paragraph in body:
            self.prev_p_info = self.cur_p_info
            self.cur_p_info = self.default_p_info.copy()

            if paragraph.pStyle:
                self.cur_p_info = self.styles_extractor.parse(paragraph.pStyle['w:val'])
                self.cur_p_info['text'] = ''
            # size
            size = paragraph.sz
            self.set_tag_value(size, 'size')
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
            else:
                self.cur_p_info['indent'] = self.prev_p_info['indent']

            # bold
            # TODO different values the same attribute in the same paragraph
            bold = paragraph.b
            self.set_tag_value(bold, 'bold')
            # TODO check the assumption
            if paragraph.pPr:
                if paragraph.pPr.b:
                    self.cur_p_info['bold'] = '1'
            # italic
            italic = paragraph.i
            self.set_tag_value(italic, 'italic')
            # underlined
            underlined = paragraph.u
            self.set_tag_value(underlined, 'underlined')

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
                pass
        else:
            self.cur_p_info[tag_name] = self.prev_p_info[tag_name]


if __name__ == "__main__":
    filename = input()
    p = DocumentParser(filename)
    lines_info = p.parse()
    for line in lines_info:
        print(line)
