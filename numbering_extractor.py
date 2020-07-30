import zipfile
from bs4 import BeautifulSoup
from styles_extractor import StylesExtractor
from properties_extractor import PropertiesExtractor
import re
import os

bad_file_num = 0
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


def get_next_item(num_fmt, shift):
    if num_fmt == "none":
        return numFmtList[num_fmt]
    if num_fmt == "decimal":
        return str(int(numFmtList[num_fmt]) + shift)
    if num_fmt == "lowerLetter" or num_fmt == "upperLetter":
        shift1, shift2 = shift % 26, shift // 26 + 1
        return chr(ord(numFmtList[num_fmt]) + shift1) * shift2
    if num_fmt == "russianLower" or num_fmt == "russianUpper":
        shift1, shift2 = shift % 32, shift // 32 + 1
        return chr(ord(numFmtList[num_fmt]) + shift1) * shift2
    if num_fmt == "lowerRoman" or num_fmt == "upperRoman":
        # 1 = I, 5 = V, 10 = X, 50 = L, 100 = C, 500 = D, 1000 = M.
        mapping = [(1000, 'm'), (500, 'd'), (100, 'c'),
                   (50, 'l'), (10, 'x'), (5, 'v'), (1, 'i')]
        result = ""
        for number, letter in mapping:
            cnt, shift = shift // number, shift % number
            if num_fmt == "upperRoman":
                letter = chr(ord(letter) + ord('A') - ord('a'))
            result += letter * cnt
        return result


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
            # styleLink-> abstractNumId of the other numbering
            self.properties['styleLink'] = tree.numStyleLink['w:val']
        else:
            self.properties['styleLink'] = None

        try:
            if tree['w15:restartNumberingAfterBreak']:
                self.properties['restart'] = bool(int(tree['w15:restartNumberingAfterBreak']))
        except KeyError:
            self.properties['restart'] = False
        # properties for each list level {level number: properties}
        self.levels = {}

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
                if lvl.numFmt:
                    self.levels[ilvl]['numFmt'] = lvl.numFmt['w:val']
                else:
                    self.levels[ilvl]['numFmt'] = 'none'

            if lvl.start:
                self.levels[ilvl]['start'] = int(lvl.start['w:val'])
            else:
                self.levels[ilvl]['start'] = 1
            if lvl.lvlRestart:
                self.levels[ilvl]['lvlRestart'] = bool(int(lvl.lvlRestart['w:val']))
            else:
                self.levels[ilvl]['lvlRestart'] = True
            if lvl.suff:
                self.levels[ilvl]['suff'] = getSuffix[lvl.suff['w:val']]
            else:
                self.levels[ilvl]['suff'] = getSuffix["tab"]

            # extract information from paragraphs and raws properties
            if lvl.pStyle:
                properties = self.styles_extractor.parse(lvl.pStyle['w:val'], "numbering")
                if properties == {'size': 0, 'indent': {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0},
                                  'bold': '0', 'italic': '0', 'underlined': 'none', 'qFormat': False}:
                    properties = self.styles_extractor.parse(lvl.pStyle['w:val'], "paragraph")
            else:
                properties = self.styles_extractor.parse(None)
            style_not_important = not properties['qFormat']
            del properties['qFormat']
            if 'numPr' in properties:
                del properties['numPr']
            # paragraph -> raw
            if lvl.pPr:
                pe = PropertiesExtractor(lvl.pPr)
                pe.get_properties(properties)
                self.levels[ilvl]['pPr'] = properties.copy()
            if lvl.rPr:
                pe = PropertiesExtractor(lvl.rPr)
                pe.get_properties(properties)
                del properties['indent']
                self.levels[ilvl]['rPr'] = properties.copy()
            else:
                self.levels[ilvl]['rPr'] = None


class Num(AbstractNum):

    def __init__(self, num_id, abstract_num_list, num_list, styles_extractor):
        # abstract_num_list - dictionary with abstractNum BeautifulSoup trees
        # num_list - dictionary with num BeautifulSoup trees
        self.num_id = num_id
        num_tree = num_list[num_id]
        abstract_num_tree = abstract_num_list[num_tree.abstractNumId['w:val']]
        super().__init__(abstract_num_tree, styles_extractor)  # create properties
        # extract the information from numStyleLink
        while self.properties['styleLink']:
            for abstract_num in abstract_num_list.values():
                if abstract_num.find('w:styleLink', attrs={'w:val': self.properties['styleLink']}):
                    abstract_num_tree = abstract_num
                    break
            super().__init__(abstract_num_tree, styles_extractor)
        self.parse(abstract_num_tree.find_all('w:lvl'))

        # override some of abstractNum properties
        if num_tree.lvlOverride:
            self.parse(num_tree.lvlOverride.find_all('w:lvl'))

    def get_level_info(self, level_num):
        return self.levels[level_num].copy()


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

        self.numerations = {}  # {(abstractNumId, ilvl): current number for list element}
        self.prev_num_id = None
        self.prev_abstract_num_id = None
        self.prev_ilvl = {}  # {abstractNumId: ilvl} previous ilvl for list element with given numId

        abstract_num_list = {abstract_num['w:abstractNumId']: abstract_num
                             for abstract_num in xml.find_all('w:abstractNum')}
        num_list = {num['w:numId']: num for num in xml.find_all('w:num')}

        # dictionary with num properties
        self.num_list = {num_id: Num(num_id, abstract_num_list, num_list, styles_extractor) for num_id in num_list}

    def get_list_text(self, ilvl, num_id):
        if num_id not in self.num_list:
            return ""
        abstract_num_id = self.num_list[num_id].abstract_num_id
        lvl_info = self.num_list[num_id].get_level_info(ilvl)
        # there is the other list
        if self.prev_abstract_num_id and self.prev_num_id and self.prev_abstract_num_id != abstract_num_id and \
                self.num_list[self.prev_num_id].properties['restart']:
            del self.prev_ilvl[self.prev_abstract_num_id]
        # there is the information about this list
        if abstract_num_id in self.prev_ilvl:
            prev_ilvl = self.prev_ilvl[abstract_num_id]
            # it's a new level
            if prev_ilvl < ilvl and lvl_info['lvlRestart'] or (abstract_num_id, ilvl) not in self.numerations:
                self.numerations[(abstract_num_id, ilvl)] = lvl_info['start']
            # it's a continue of the old level
            else:
                self.numerations[(abstract_num_id, ilvl)] += 1
        # there isn't the information about this list
        else:
            self.numerations[(abstract_num_id, ilvl)] = lvl_info['start']
        self.prev_ilvl[abstract_num_id] = ilvl
        self.prev_abstract_num_id = abstract_num_id
        self.prev_num_id = num_id

        text = lvl_info['lvlText']
        levels = re.findall(r'%\d+', text)
        for level in levels:
            # level = '%level'
            level = level[1:]
            text = re.sub(r'%\d+', self.get_next_number(num_id, level), text, count=1)
        text += lvl_info['suff']
        return text

    def get_next_number(self, num_id, level):
        abstract_num_id = self.num_list[num_id].abstract_num_id
        # level = ilvl + 1
        ilvl = str(int(level) - 1)
        lvl_info = self.num_list[num_id].get_level_info(ilvl)

        try:
            shift = self.numerations[(abstract_num_id, ilvl)] - 1
        except KeyError:
            # TODO handle very strange list behaviour
            # print('=================')
            # print("abstractNumId = {}, ilvl = {}".format(abstract_num_id, ilvl))
            # print('=================')
            # if we haven't found given abstractNumId we use previous
            shift = self.numerations[(self.prev_abstract_num_id, ilvl)] - 1
            # return ""

        if lvl_info['numFmt'] == "bullet":
            num_fmt = lvl_info['lvlText']
        else:
            num_fmt = get_next_item(lvl_info['numFmt'], shift)
        return num_fmt

    def parse(self, xml):
        # xml - BeautifulSoup tree with numPr from document.xml
        # in the paragraph properties of the list
        # the method the text and properties of the list element
        # returns dict:
        # {"text": text of list element,
        # "pPr": {'size': 0, 'indent': {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0},
        # 'bold': '0', 'italic': '0', 'underlined': 'none'}, "rPr": None or
        # {'size': 0, 'bold': '0', 'italic': '0', 'underlined': 'none'} for text }
        if not xml:
            return None
        ilvl, num_id = xml.ilvl, xml.numId
        if not ilvl:
            ilvl = '0'
        else:
            ilvl = ilvl['w:val']
        if not num_id:
            return None
        else:
            num_id = num_id['w:val']
        # try:
        #     ilvl, num_id = ilvl['w:val'], num_id['w:val']
        #     lvl_info = self.num_list[num_id].get_level_info(ilvl)
        #     text = self.get_list_text(ilvl, num_id)
        #     return {"text": text, "lvl": ilvl, "pPr": lvl_info['pPr'], "rPr": lvl_info['rPr']}
        # except KeyError:
        #     print('error in numbering parse')
        #     return None
        lvl_info = self.num_list[num_id].get_level_info(ilvl)
        text = self.get_list_text(ilvl, num_id)
        return {"text": text, "lvl": ilvl, "pPr": lvl_info['pPr'], "rPr": lvl_info['rPr']}


if __name__ == "__main__":
    wrong_files = []
    bad_zip_files = []
    file_without_lists = 0
    i = 0
    choice = input()
    if choice == 'test':
        filenames = os.listdir('examples/docx/docx')
    else:
        filenames = [choice]
    total = len(filenames)
    for filename in filenames:
        i += 1
        # document = zipfile.ZipFile('examples/' + filename)
        try:
            if choice == "test":
                document = zipfile.ZipFile('examples/docx/docx/' + filename)
            else:
                document = zipfile.ZipFile('examples/' + filename)
            try:
                numbering_bs = BeautifulSoup(document.read('word/numbering.xml'), 'xml')
            except KeyError:
                file_without_lists += 1
            else:
                document_bs = BeautifulSoup(document.read('word/document.xml'), 'xml')
                styles_bs = BeautifulSoup(document.read('word/styles.xml'), 'xml')
                se = StylesExtractor(styles_bs)
                ne = NumberingExtractor(numbering_bs, se)
                for paragraph in document_bs.body:
                    if choice != 'test':
                        paragraph_text = map(lambda x: x.text, paragraph.find_all('w:t'))
                        res = ""
                        for item in paragraph_text:
                            res += item
                    else:
                        res = ""
                    if paragraph.numPr:
                        p_properties = ne.parse(paragraph.numPr)
                        if choice != 'test':
                            print(p_properties)
                            print(res)
                    else:
                        if choice != 'test':
                            print(res)
            if choice == 'test':
                print(f"\r{i} objects are processed...", end='', flush=True)
        except zipfile.BadZipFile:
            bad_zip_files.append(filename)
        except KeyError:
            bad_file_num += 1
            wrong_files.append(filename)
    # total: 2193, bad files: 371, without lists: 289
    if choice == 'test':
        print('total: {}, bad files: {}, without lists: {}'.format(total, bad_file_num, file_without_lists))
        print('bad zip: ', bad_zip_files)
        print('wrong_files: ', wrong_files)
    # wrong_files:  ['doc_002400.docx', 'doc_002050.docx', 'doc_000201.docx', 'doc_001410.docx', 'doc_001555.docx',
    # 'doc_000485.docx', 'doc_000606.docx', 'doc_000885.docx', 'doc_000186.docx', 'doc_002504.docx', 'doc_002857.docx',
    # 'doc_001902.docx', 'doc_000581.docx', 'doc_001406.docx', 'doc_003084.docx', 'doc_001754.docx', 'doc_001216.docx']
