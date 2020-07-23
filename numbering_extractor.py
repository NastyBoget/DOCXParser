import zipfile
from bs4 import BeautifulSoup
from collections import defaultdict
from styles_extractor import StylesExtractor
import re

# pages 691 - 733 in the documentation

# page 1424
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

# page 1402
getSuffix = {"nothing": "",
             "space": " ",
             "tab": "\t"}


class AbstractNum:

    def __init__(self, tree, styles_extractor):
        # tree - BeautifulSoup tree with abstractNum content
        # styles - StylesExtractor
        self.styles_extractor = styles_extractor
        self.abstract_num_id = tree['w:abstractNumId']
        self.properties = {}  # properties for all levels

        if tree.numStyleLink:
            style_id = tree.numStyleLink['w:val']
            style = self.styles_extractor.styles.find('w:style', attrs={'w:styleId': style_id, 'w:type': 'numbering'})
            self.properties['numId'] = style.numId['w:val']  # numId -> abstractNumId of the other numbering
        else:
            self.properties['numId'] = None
        # TODO extract style
        if tree.styleLink:
            self.properties['style'] = tree.styleLink['w:val']
        try:
            if tree['restartNumberingAfterBreak']:
                self.properties['restart'] = bool(int(tree['restartNumberingAfterBreak']))
        except KeyError:
            self.properties['restart'] = True
        # properties for each list level {level number: properties}
        self.levels = {}
        self.parse(tree.find_all('w:lvl'))

    def parse(self, lvl_list):
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
        for lvl in lvl_list:
            ilvl = lvl['w:ilvl']
            if ilvl not in self.levels:
                self.levels[ilvl] = {}
            if lvl.lvlText:
                self.levels[ilvl]['lvlText'] = lvl.lvlText['w:val']

            if lvl.isLgl:
                self.levels[ilvl]['numFmt'] = 'decimal'
            else:
                self.levels[ilvl]['numFmt'] = lvl.numFmt['w:val']

            if lvl.start:
                self.levels[ilvl]['start'] = int(lvl.start['w:val'])

            if lvl.lvlRestart:
                self.levels[ilvl]['lvlRestart'] = bool(int(lvl.lvlRestart['w:val']))
            else:
                self.levels[ilvl]['lvlRestart'] = True
            # TODO extract information from paragraphs and raws properties
            if lvl.suff:
                self.levels[ilvl]['suff'] = getSuffix[lvl.suff['w:val']]
            else:
                self.levels[ilvl]['suff'] = getSuffix["tab"]

            if 'numFmt' in self.levels[ilvl] and self.levels[ilvl]['numFmt'] == "bullet":
                self.levels[ilvl]['firstItem'] = self.levels[ilvl]['lvlText']
            elif 'numFmt' in self.levels[ilvl]:
                self.levels[ilvl]['firstItem'] = numFmtList[self.levels[ilvl]['numFmt']]


class Num(AbstractNum):

    def __init__(self, num_id, abstract_num_list, num_list, styles_extractor):
        # abstract_num_list - dictionary with abstractNum BeautifulSoup trees
        # num_list - dictionary with num BeautifulSoup trees
        self.num_id = num_id
        num_tree = num_list[num_id]
        abstract_num_tree = abstract_num_list[num_tree.abstractNumId['w:val']]
        super().__init__(abstract_num_tree, styles_extractor)  # create properties
        # extract the information from numStyleLink
        while self.properties['numId']:
            # extract levels info from Num but not from AbstractNum
            abstract_num_id = num_list[self.properties['numId']].abstractNumId['w:val']
            abstract_num_tree = abstract_num_list[abstract_num_id]
            super().__init__(abstract_num_tree, styles_extractor)

        # override some of abstractNum properties
        if num_tree.lvlOverride:
            self.parse(num_tree.lvlOverride.find_all('w:lvl'))

    def get_level_info(self, level_num):
        return self.levels[level_num]


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

        self.numerations = defaultdict(int)  # {(numId, ilvl): current number for list element}
        self.prev_lvl = None  # previous list level in the document

        abstract_num_list = {abstract_num['w:abstractNumId']: abstract_num
                             for abstract_num in xml.find_all('w:abstractNum')}
        num_list = {num['w:numId']: num for num in xml.find_all('w:num')}

        # dictionary with num properties
        self.num_list = {num_id: Num(num_id, abstract_num_list, num_list, styles_extractor) for num_id in num_list}

    def get_list_text(self, ilvl, num_id):
        if num_id not in self.num_list:
            return ""

        lvl_info = self.num_list[num_id].get_level_info(ilvl)

        # TODO more accurate restarting
        if self.prev_lvl:
            # TODO prev level may be with other numId!!!
            prev_lvl_info = self.num_list[num_id].get_level_info(self.prev_lvl)
            if self.prev_lvl >= ilvl:
                self.numerations[(num_id, ilvl)] += 1
                if self.prev_lvl > ilvl and prev_lvl_info['lvlRestart']:
                    self.numerations[(num_id, self.prev_lvl)] = prev_lvl_info['start'] - 1
            else:
                self.numerations[(num_id, ilvl)] = lvl_info['start']
        else:
            self.numerations[(num_id, ilvl)] = lvl_info['start']
        self.prev_lvl = ilvl

        text = lvl_info['lvlText']

        levels = re.findall(r'%\d+', text)
        for level in levels:
            # level = ilvl + 1
            level = level[1:]
            text = re.sub(r'%\d+', self.get_next_number(num_id, level), text, count=1)
        text += lvl_info['suff']
        return text

    def get_next_number(self, num_id, level):
        # level = ilvl + 1
        ilvl = str(int(level) - 1)
        lvl_info = self.num_list[num_id].get_level_info(ilvl)

        if not self.numerations[(num_id, ilvl)]:
            self.numerations[(num_id, ilvl)] += 1
        shift = self.numerations[(num_id, ilvl)] - 1

        # TODO more types of lists
        if lvl_info['numFmt'] == "bullet":
            num_fmt = lvl_info['firstItem']
        elif lvl_info['numFmt'] == "none":
            num_fmt = ""
        else:
            num_fmt = chr(ord(lvl_info['firstItem']) + shift)
        return num_fmt

    def parse(self, xml):  # TODO
        # xml - # xml - BeautifulSoup tree with document.xml
        # the method finds lists elements in the document and extracts the text and properties of these elements
        # returns dict:
        # {"text": text of list element, "lvl" : level within document according to xml file,
        # "properties": {'size': 0, 'indent': 0, 'bold': '0', 'italic': '0', 'underlined': 'none'}}
        pass


if __name__ == "__main__":
    filename = input()
    document = zipfile.ZipFile('examples/' + filename)
    try:
        numbering_bs = BeautifulSoup(document.read('word/numbering.xml'), 'xml')
    except KeyError:
        print(document.namelist())
    else:
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
