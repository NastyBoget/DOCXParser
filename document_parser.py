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
        self.default_p_info = {'text': '', 'properties': [[0, 0, self.styles_extractor.parse(None)]]}  # default style
        self.cur_p_info = self.default_p_info.copy()

    def parse(self):
        # returns the list of dictionaries for each paragraph
        # [{"text": "", "properties": [[start, end, {indent, size, bold, italic, underlined}], ...] }, ...]
        # start, end - character's positions begin with 0, end isn't included

        body = self.document_bs.body
        if not body:
            return self.data

        for paragraph in body:

            if paragraph.pStyle:
                style_info = self.styles_extractor.parse(paragraph.pStyle['w:val'])
            else:
                style_info = self.default_p_info['properties'][0][2]
            self.cur_p_info = {'text': '', 'properties': []}

            # indent
            # TODO different attributes for indent
            # TODO more accurate with previous paragraphs
            # indent is common for all runs in the paragraph
            indent = style_info['indent']
            if paragraph.ind:
                try:
                    indent = int(paragraph.ind['w:firstLine'])
                except KeyError:
                    try:
                        indent = int(paragraph.ind['w:left'])
                    except KeyError:
                        pass

            raw_list = paragraph.find_all('w:r')
            prev_properties = style_info.copy()
            for raw in raw_list:
                # text
                if not raw.t or not raw.t.text:
                    continue
                start, end = len(self.cur_p_info['text']), len(self.cur_p_info['text']) + len(raw.t.text)
                if not self.cur_p_info['text']:
                    self.cur_p_info['text'] = raw.t.text
                else:
                    self.cur_p_info['text'] += raw.t.text

                # size
                # 1) properties in style
                # 2) properties in the paragraph
                # 3) properties in the raw
                size = style_info['size']
                if paragraph.pPr:
                    res = self.get_tag_value(paragraph.pPr.sz)
                    if res:
                        size = res
                res = self.get_tag_value(raw.sz)
                if res:
                    size = res
                size = int(size)

                # bold
                # tag b in styles without value means '1'
                # tag b in pPr without value means '1'
                bold = style_info['bold']
                if paragraph.pPr:
                    res = self.get_tag_value(paragraph.pPr.b, '1')
                    if res:
                        bold = res
                res = self.get_tag_value(raw.b, '1')
                if res:
                    bold = res

                # italic
                italic = style_info['italic']
                if paragraph.pPr:
                    res = self.get_tag_value(paragraph.pPr.i, '1')
                    if res:
                        italic = res
                res = self.get_tag_value(raw.i, '1')
                if res:
                    italic = res

                # underlined
                underlined = style_info['underlined']
                if paragraph.pPr:
                    res = self.get_tag_value(paragraph.pPr.u, 'none')
                    if res:
                        underlined = res
                res = self.get_tag_value(raw.u, 'none')
                if res:
                    underlined = res

                cur_properties = {'indent': indent, 'size': size,
                                  'bold': bold, 'italic': italic, 'underlined': underlined}
                if prev_properties == cur_properties and self.cur_p_info['properties']:
                    self.cur_p_info['properties'][-1][1] = end  # change the end of such style
                else:
                    self.cur_p_info['properties'].append([start, end, cur_properties])
                    prev_properties = cur_properties

            self.data.append(self.cur_p_info.copy())

        return self.data

    @staticmethod
    def get_tag_value(tag, default=None):
        value = None
        if tag:
            try:
                value = tag['w:val']
            except KeyError:
                if default:
                    value = default
        return value


if __name__ == "__main__":
    filename = input()
    p = DocumentParser(filename)
    lines_info = p.parse()
    for line in lines_info:
        print(line['text'])
        for raw_info in line['properties']:
            print('start={} end={} properties={}'.format(raw_info[0], raw_info[1], raw_info[2]))
        print()
