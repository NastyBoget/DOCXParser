import zipfile
from bs4 import BeautifulSoup


class PropertiesExtractor:

    def __init__(self, tree):
        # tree - BeautifulSoup tree with properties
        if tree:
            self.tree = tree
        else:
            raise ValueError("tree mustn't be None")

    def get_properties(self, old_properties):
        # returns dictionary with properties if they were found
        # changes old properties which should be like the following dictionary:
        # {'size': 0, 'indent': {}, 'bold': '0', 'italic': '0', 'underlined': 'none'}
        # indent = {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0} TODO firstLineChars etc.

        # size
        if self.tree.sz:
            try:
                old_properties['size'] = int(self.tree.sz['w:val'])
            except KeyError:
                pass
        # indent
        if self.tree.ind:
            indent_properties = ['firstLine', 'hanging', 'start', 'left']
            for indent_property in indent_properties:
                try:
                    old_properties['indent'][indent_property] = int(self.tree.ind['w:' + indent_property])
                except KeyError:
                    pass

        # bold
        if self.tree.b:
            try:
                old_properties['bold'] = self.tree.b['w:val']
            except KeyError:
                old_properties['bold'] = '1'

        # italic
        if self.tree.i:
            try:
                old_properties['italic'] = self.tree.i['w:val']
            except KeyError:
                old_properties['italic'] = '1'

        # underlined
        if self.tree.u:
            try:
                old_properties['underlined'] = self.tree.u['w:val']
            except KeyError:
                pass


if __name__ == "__main__":
    filename = input()
    document = zipfile.ZipFile('examples/' + filename)
    document_bs = BeautifulSoup(document.read('word/document.xml'), 'xml')
    for p in document_bs.body:
        if p.pPr:
            pe = PropertiesExtractor(p.pPr)
            properties = {'size': 0, 'indent': {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0},
                          'bold': '0', 'italic': '0', 'underlined': 'none'}
            pe.get_properties(properties)
            print(properties)
