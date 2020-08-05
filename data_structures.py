from bs4 import BeautifulSoup
from properties_extractor import change_properties


class BaseProperties:

    def __init__(self,
                 xml: BeautifulSoup or None,
                 styles_extractor):
        self.size = 0
        self.indent = {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0}
        self.bold = False
        self.italic = False
        self.underlined = False
        self.xml = xml
        self.styles_extractor = styles_extractor


class Paragraph(BaseProperties):

    def __init__(self,
                 xml: BeautifulSoup,
                 styles_extractor,
                 numbering_extractor):

        self.numbering_extractor = numbering_extractor
        self.raws = []
        self.r_pr = None  # rPr from styles
        super().__init__(xml, styles_extractor)
        self.parse()

    def parse(self):
        # hierarchy: properties in styles -> direct properties (paragraph, character)
        # 1) documentDefault (styles.xml)
        # 2) tables (styles.xml)
        # 3) paragraphs styles (styles.xml)
        # 4) numbering styles (styles.xml, numbering.xml)
        # 5) characters styles (styles.xml)
        # 6) paragraph direct formatting (document.xml)
        # 7) numbering direct formatting (document.xml, numbering.xml)
        # 8) character direct formatting (document.xml)

        # 1) docDefaults
        self.styles_extractor.parse(None, self, "paragraph")
        # 2) we ignore tables

        # 3) paragraph styles
        # 4) numbering styles within styles_extractor
        if self.xml.pStyle:
            self.styles_extractor.parse(self.xml.pStyle['w:val'], self, "paragraph")

        # 5) character style parsed later for each raw TODO check if there are character styles for paragraphs
        # 6) paragraph direct formatting
        if self.xml.pPr:
            change_properties(self, self.xml.pPr)
        # 7) numbering direct formatting
        if self.xml.numPr and self.numbering_extractor:
            try:
                numbering_raw = Raw(self, self.styles_extractor, self.r_pr)
                self.numbering_extractor.parse(self.xml.numPr, self, numbering_raw)
                self.raws.append(numbering_raw)
            except KeyError as error:
                print(error)

        # 8) character direct formatting
        raw_list = self.xml.find_all('w:r')
        for raw_tree in raw_list:
            new_raw = Raw(raw_tree, self.styles_extractor, self.r_pr)
            if not new_raw.text:
                continue
            if not new_raw.size:
                new_raw.size = self.size
            if self.raws and self.raws[-1] == new_raw:
                # it's is not completely correct because of incorrect information in raw
                self.raws[-1].text += new_raw.text
            else:
                self.raws.append(new_raw)

    def get_info(self):
        """
        :return: dictionary {"text": "",
        "properties": [[start, end, {"indent", "size", "bold", "italic", "underlined"}], ...] }
        start, end - character's positions begin with 0, end isn't included
        indent = {"firstLine", "hanging", "start", "left"}
        """
        line_metadata = {"text": "", "properties": []}
        for raw in self.raws:
            start, end = len(line_metadata['text']), len(line_metadata['text']) + len(raw.text)
            if not line_metadata['text']:
                line_metadata['text'] = raw.text
            else:
                line_metadata['text'] += raw.text
            properties = dict()
            properties['indent'] = self.indent.copy()
            if raw.size:
                properties['size'] = raw.size
            else:
                properties['size'] = self.size
            properties['bold'] = raw.bold
            properties['italic'] = raw.italic
            properties['underlined'] = raw.underlined
            line_metadata['properties'].append([start, end, properties])

        return line_metadata


class Raw(BaseProperties):

    def __init__(self,
                 xml: BeautifulSoup or BaseProperties,
                 styles_extractor,
                 style=None):

        self.text = ""
        self.style = style
        super().__init__(xml, styles_extractor)
        if isinstance(xml, BaseProperties):
            self.xml = None
            self.size = xml.size
            if style:
                self.underlined = style.underlined
                self.bold = style.bold
                self.italic = style.italic
        else:
            self.parse()

    def parse(self):
        for tag in self.xml:
            if tag.name == 't' and tag.text:
                self.text += tag.text
            elif tag.name == 'tab':
                self.text += '\t'
            elif tag.name == 'br':
                self.text += '\n'
            elif tag.name == 'cr':
                self.text += '\r'
            elif tag.name == 'sym':
                pass  # TODO

        # TODO solve this more correctly
        if self.style:
            self.size = self.style.size
            self.underlined = self.style.underlined
            self.bold = self.style.bold
            self.italic = self.style.italic
        if self.xml.rStyle:
            # TODO rStyle before pPr
            self.styles_extractor.parse(self.xml.rStyle['w:val'], self, "character")

        if self.xml.rPr:
            change_properties(self, self.xml.rPr)  # TODO in different documents different behavior

    def __eq__(self, other):
        if other:
            return self.size == other.size and self.bold == other.bold \
                   and self.italic == other.italic and self.underlined == other.underlined
        else:
            return False

