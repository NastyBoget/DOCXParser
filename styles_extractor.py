import zipfile
from bs4 import BeautifulSoup


class StylesExtractor:

    def __init__(self, xml):
        # xml - BeautifulSoup tree with styles
        if xml:
            self.styles = xml.find('w:styles')
            if not self.styles:
                raise Exception("there are no styles")
        else:
            raise Exception("xml must not be empty")
        # default style
        self.default_info = self.parse(None)

    def find_style(self, style_id):
        # finds style tree with given style_id
        # if there isn't such style, returns None
        # style type may be "paragraph", "numbering" or None for custom styles
        styles = self.styles.find_all('w:style', attrs={'w:styleId': style_id})
        result_style = None
        for style in styles:
            try:
                if style['w:type'] == 'paragraph' or style['w:type'] == 'numbering':
                    return style
            except KeyError:
                result_style = style
        return result_style

    def parse(self, style_id):
        # if tag b, i presents, but there isn't its value, then propose w:val = '0'
        # for tag u value = 'none'
        # for indent and size value = 0
        # if style_id is None finds default style
        # returns dictionary with properties if the style was found
        # else returns default properties or the following dictionary:
        # {'size': 0, 'indent': 0, 'bold': '0', 'italic': '0', 'underlined': 'none'}

        # TODO basedOn
        # TODO numbering is more important
        # TODO aliases, name
        # TODO qFormat
        # TODO information in numPr for indent

        if not style_id:
            style = self.styles.find('w:docDefaults')
            p_info = {'size': 0, 'indent': 0, 'bold': '0', 'italic': '0', 'underlined': 'none'}
        else:
            style = self.find_style(style_id)
            p_info = self.default_info
        if not style:
            return p_info

        # size
        size = style.find('sz')
        if size:
            try:
                p_info['size'] = int(size['w:val'])
            except KeyError:
                pass
        # indent
        # TODO different attributes for indent
        indent = style.find('ind')
        if indent:
            try:
                p_info['indent'] = int(indent['w:firstLine'])
            except KeyError:
                try:
                    p_info['indent'] = int(indent['w:left'])
                except KeyError:
                    pass
        # bold
        # TODO find out the behaviour if there isn't value attribute
        bold = style.find('b')
        if bold:
            try:
                p_info['bold'] = bold['w:val']
            except KeyError:
                pass

        # italic
        italic = style.find('i')
        if italic:
            try:
                p_info['italic'] = italic['w:val']
            except KeyError:
                pass

        # underlined
        underlined = style.find('u')
        if underlined:
            try:
                p_info['underlined'] = underlined['w:val']
            except KeyError:
                pass
        return p_info


if __name__ == "__main__":
    filename = input()
    document = zipfile.ZipFile('examples/' + filename)
    bs = BeautifulSoup(document.read('word/styles.xml'), 'xml')
    style_ids = []
    for possible_style in bs.find_all('style'):
        try:
            style_ids.append(possible_style['w:styleId'])
        except KeyError:
            pass
    print(style_ids)
    s = StylesExtractor(bs)
    default = {'size': 0, 'indent': 0, 'bold': '0', 'italic': '0', 'underlined': 'none'}
    for styleId in style_ids:
        res = s.parse(styleId)
        if res and res != default:
            print(res)
