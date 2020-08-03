import zipfile
from bs4 import BeautifulSoup
from properties_extractor import PropertiesExtractor


# page 665 in documentation

class StylesExtractor:

    def __init__(self, xml):
        # xml - BeautifulSoup tree with styles
        if xml:
            self.styles = xml.styles
            if not self.styles:
                raise Exception("there are no styles")
        else:
            raise Exception("xml must not be empty")

    def find_style(self, style_id, style_type='paragraph'):
        # style_type may be paragraph, numbering or character
        # finds style tree with given style_id and type
        # if there isn't such style, returns None
        # style type may be "paragraph", "numbering", "character", or None for custom styles
        styles = self.styles.find_all('w:style', attrs={'w:styleId': style_id})
        result_style = None
        for style in styles:
            try:
                if style['w:type'] == style_type:
                    return style
            except KeyError:
                result_style = style
        return result_style

    def parse(self, style_id, style_type='paragraph'):
        # if tag b, i presents, but there isn't its value, then w:val = '1'
        # for tag u value = 'none'
        # for indent and size value = 0
        # if style_id is None finds default style
        # returns dictionary with properties if the style was found
        # else returns default properties or the following dictionary:
        # {'size': 0, 'indent': {}, 'bold': '0', 'italic': '0', 'underlined': 'none'}
        # indent = {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0,
        # 'numPr': style.numPr (optional)}
        # TODO firstLineChars etc.

        info = {'size': 0, 'indent': {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0},
                'bold': '0', 'italic': '0', 'underlined': 'none'}

        default_style = self.styles.find_all('w:style', attrs={'w:default': "1", 'w:type': style_type})
        if default_style:
            default_style = default_style[0]
        elif self.styles.docDefaults:
            default_style = self.styles.docDefaults

        if not style_id:
            if default_style:
                pe = PropertiesExtractor(default_style)
                pe.get_properties(info)
            return info

        # TODO hierarchy of styles: defaults -> paragraph -> numbering -> character
        styles = []
        style = self.find_style(style_id, style_type)
        if not style:
            return info

        # TODO information in numPr for styles
        # TODO link
        # TODO suppressLineNumbers
        if style.numPr:
            info['numPr'] = style

        # basedOn + hierarchy of styles
        current_style = style
        while current_style.basedOn:
            try:
                parent_style_id = current_style.basedOn['w:val']
                current_style = self.find_style(parent_style_id, style_type)
                if current_style:
                    styles.append(current_style)
            except KeyError:
                pass

        styles = styles[::-1] + [style]
        if default_style:
            styles = [default_style] + styles

        # TODO rPr and pPr in styles
        for style in styles:  # apply styles in reverse order
            pe = PropertiesExtractor(style)
            pe.get_properties(info)

        return info


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
    default = {'size': 0, 'indent': {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0},
               'bold': '0', 'italic': '0', 'underlined': 'none'}
    for styleId in style_ids:
        res = s.parse(styleId)
        if res and res != default:
            print(res)
