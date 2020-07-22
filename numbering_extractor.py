import zipfile
from bs4 import BeautifulSoup
from collections import defaultdict
from styles_extractor import StylesExtractor
import re


numFmtList = {"bullet": "●",  # value in lvlText
              "decimal": "1",  # 1, 2, 3, ..., 10, 11, 12, ...
              "lowerLetter": "a",  # a, b, c, ..., y, z, aa, bb, cc, ..., yy, zz, aaa, bbb, ccc, ...
              "lowerRoman": "i",  # i, ii, iii, iv, ..., xviii, xix, xx, xxi, ...
              "none": "",
              "russianLower": "а",  # а, б, в, ..., ю, я, аа, бб, вв, ..., юю, яя, ааа, ббб, ввв, ...
              "russianUpper": "А",  # А, Б, В, ..., Ю, Я, АА, ББ, ВВ, ..., ЮЮ, ЯЯ, ААА, БББ, ВВВ, ...
              "upperLetter": "A",  # A, B, C, ..., Y, Z, AA, BB, CC, ..., YY, ZZ, AAA, BBB, CCC, ...
              "upperRoman": "I",  # I, II, III, IV, ..., XVIII, XIX, XX, XXI, ...
              }

getSuffix = {"nothing": "",  # page 1402
             "space": " ",
             "tab": "\t"}


class AbstractNum:

    def __init__(self, tree):
        # tree - BeautifulSoup tree with abstractNum content
        self.tree = tree
        self.abstract_num_id = tree['w:abstractNumId']
        self.lvl_list = tree.find_all('w:lvl')
        self.properties = {}  # properties for all levels
        # properties for each list level {level number: properties}
        self.levels = {}
        self.parse()

    def parse(self):
        # TODO extract style
        if self.tree.numStyleLink:
            self.properties['style'] = self.tree.numStyleLink['w:val']
        if self.tree.styleLink:
            self.properties['style'] = self.tree.styleLink['w:val']
        try:
            if self.tree['restartNumberingAfterBreak']:
                self.properties['restart'] = bool(int(self.tree['restartNumberingAfterBreak']))
        except KeyError:
            self.properties['restart'] = True

        # isLgl (only mention)
        # lvlText (val="some text %num some text")
        # numFmt (val="bullet", "decimal")
        # pPr -> ind
        # pStyle -> pPr
        # rPr -> sz, bold, italic, underlined
        # start (w:val="1")
        # suff (w:val="nothing", "tab" - default, "space")
        # lvlJc (Justification, val="start", "end")
        # lvlRestart (w:val="0")
        for lvl in self.lvl_list:
            lvl_info = dict()
            lvl_info['lvlText'] = lvl.lvlText['w:val']
            if lvl.isLgl:
                lvl_info['numFmt'] = 'decimal'
            else:
                lvl_info['numFmt'] = lvl.numFmt['w:val']
            lvl_info['start'] = int(lvl.start['w:val'])
            if lvl.lvlRestart:
                lvl_info['lvlRestart'] = bool(int(lvl.lvlRestart['w:val']))
            else:
                lvl_info['lvlRestart'] = True
            # TODO extract information from paragraphs and raws properties
            if lvl.suff:
                lvl_info['suff'] = getSuffix[lvl.suff['w:val']]
            else:
                lvl_info['suff'] = getSuffix["tab"]
            if lvl_info['numFmt'] == "bullet":
                lvl_info['firstItem'] = lvl_info['lvlText']
            else:
                lvl_info['firstItem'] = numFmtList[lvl_info['numFmt']]
            self.levels[lvl['w:ilvl']] = lvl_info.copy()

    def get_properties(self):
        return self.properties

    def get_levels(self):
        return self.levels

    def get_level_info(self, level_num):
        return self.levels[level_num]


class Num:

    def __init__(self, tree):
        # tree - BeautifulSoup tree with num content
        self.num_id = tree['w:numId']
        self.abstract_num_id = tree.abstractNumId['w:val']
        self.lvl_override = tree.lvlOverride
        # TODO lvlOverride processing

    def get_abstract_num_id(self):
        return self.abstract_num_id


class NumberingExtractor:

    def __init__(self, xml, styles_extractor):

        # xml - BeautifulSoup tree with numberings
        if xml:
            self.numbering = xml.numbering
            if not self.numbering:
                raise Exception("there are no numbering")
        else:
            raise Exception("xml must not be empty")

        if styles_extractor:
            self.styles_extractor = styles_extractor
        else:
            raise Exception("styles extractor must not be empty")

        self.numerations = defaultdict(int)  # {numId: current number for list element}
        self.prev_lvl = None  # previous list level in the document

        # dictionary with abstractNum properties
        self.abstract_num_list = {abstract_num['w:abstractNumId']: AbstractNum(abstract_num)
                                  for abstract_num in xml.find_all('w:abstractNum')}

        try:
            # dictionary with num properties
            self.num_list = {num['w:numId']: Num(num) for num in xml.find_all('w:num')}
        except KeyError:
            raise Exception("wrong numbering.xml file")

    def get_list_text(self, ilvl, num_id):
        if num_id not in self.num_list:
            return ""

        abstract_num = self.abstract_num_list[self.num_list[num_id].get_abstract_num_id()]
        lvl_info = abstract_num.get_level_info(ilvl)

        if self.prev_lvl:
            # if self.prev_lvl >= ilvl:
            self.numerations[(num_id, ilvl)] += 1  # not count lvlRestart
            # else:
            #     self.numerations[(num_id, ilvl)] = lvl_info['start']
        else:
            self.numerations[(num_id, ilvl)] = lvl_info['start']
        self.prev_lvl = ilvl

        text = lvl_info['lvlText']

        levels = re.findall(r'%\d+', text)
        for level in levels:
            level = level[1:]
            text = re.sub(r'\d+%', self.get_next_number(num_id, level), text[::-1], count=1)[::-1]
        text += lvl_info['suff']
        return text

    def get_next_number(self, num_id, ilvl):
        abstract_num = self.abstract_num_list[self.num_list[num_id].get_abstract_num_id()]
        lvl_info = abstract_num.get_level_info(ilvl)

        if self.numerations[(num_id, ilvl)]:
            shift = self.numerations[(num_id, ilvl)] - 1
        else:
            self.numerations[(num_id, ilvl)] += 1
            shift = 0

        # TODO more types of lists
        if lvl_info['numFmt'] == "bullet":
            num_fmt = lvl_info['firstItem']
        elif lvl_info['numFmt'] == "none":
            num_fmt = ""
        else:
            num_fmt = chr(ord(lvl_info['firstItem']) + shift)
        return num_fmt

    def parse(self, xml):
        # xml - # xml - BeautifulSoup tree with document.xml
        # the method finds lists elements in the document and extracts the text and properties of these elements
        # returns dict:
        # {"text": text of list element, "lvl" : level within document according to xml file,
        # "properties": {'size': 0, 'indent': 0, 'bold': '0', 'italic': '0', 'underlined': 'none'}}
        pass


if __name__ == "__main__":
    filename = input()
    document = zipfile.ZipFile('examples/' + filename)
    numbering_bs = BeautifulSoup(document.read('word/numbering.xml'), 'xml')
    document_bs = BeautifulSoup(document.read('word/document.xml'), 'xml')
    styles_bs = BeautifulSoup(document.read('word/styles.xml'), 'xml')
    se = StylesExtractor(styles_bs)
    ne = NumberingExtractor(numbering_bs, se)
    for paragraph in document_bs.body:
        if paragraph.numPr:
            ilvl = paragraph.numPr.ilvl['w:val']
            numId = paragraph.numPr.numId['w:val']
            list_text = ne.get_list_text(ilvl, numId)
            paragraph_text = map(lambda x: x.text, paragraph.find_all('w:t'))
            res = ""
            for item in paragraph_text:
                res += item
            print(list_text + res)
