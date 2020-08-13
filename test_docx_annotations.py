import unittest
from document_parser import DOCXParser


class TestDocxAnnotations(unittest.TestCase):

    def test_example_1(self):
        docx_reader = DOCXParser('examples/example_1.docx')
        lines_with_meta = docx_reader.get_lines_with_meta()
        zero_indent = {"firstLine": 0, "hanging": 0, "start": 0, "left": 0}
        # bold, italic, underlined, size tests
        self.assertEqual([0, len(lines_with_meta[0]['text']),
                          {"indent": zero_indent, "size": 22, "alignment": "left",
                           "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[0]['properties'][0])
        self.assertEqual([0, len(lines_with_meta[1]['text']),
                          {"indent": zero_indent, "size": 24, "alignment": "left",
                           "bold": False, "italic": True, "underlined": False}],
                         lines_with_meta[1]['properties'][0])
        self.assertEqual([0, len(lines_with_meta[2]['text']),
                          {"indent": zero_indent, "size": 24, "alignment": "left",
                           "bold": True, "italic": False, "underlined": False}],
                         lines_with_meta[2]['properties'][0])
        self.assertEqual([0, len(lines_with_meta[3]['text']),
                          {"indent": zero_indent, "size": 24, "alignment": "left",
                           "bold": False, "italic": False, "underlined": True}],
                         lines_with_meta[3]['properties'][0])
        self.assertEqual([0, 6, {"indent": zero_indent, "size": 26, "alignment": "left",
                                 "bold": False, "italic": True, "underlined": False}],
                         lines_with_meta[4]['properties'][0])
        self.assertEqual([6, 16, {"indent": zero_indent, "size": 26, "alignment": "left",
                                  "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[4]['properties'][1])
        self.assertEqual([0, 8, {"indent": zero_indent, "size": 28, "alignment": "left",
                                 "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[5]['properties'][0])
        self.assertEqual([8, 12, {"indent": zero_indent, "size": 28, "alignment": "left",
                                  "bold": True, "italic": False, "underlined": False}],
                         lines_with_meta[5]['properties'][1])
        self.assertEqual([0, 5, {"indent": zero_indent, "size": 22, "alignment": "left",
                                 "bold": True, "italic": False, "underlined": False}],
                         lines_with_meta[6]['properties'][0])
        self.assertEqual([5, 19, {"indent": zero_indent, "size": 22, "alignment": "left",
                                  "bold": True, "italic": False, "underlined": True}],
                         lines_with_meta[6]['properties'][1])
        # indent, alignment tests
        self.assertEqual([0, 13, {"indent": zero_indent, "size": 22, "alignment": "center",
                                  "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[8]['properties'][0])
        self.assertEqual([0, 10, {"indent": zero_indent, "size": 22, "alignment": "right",
                                  "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[9]['properties'][0])
        self.assertEqual([0, 28, {"indent": zero_indent, "size": 22, "alignment": "both",
                                  "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[10]['properties'][0])
        self.assertEqual([0, 10, {"indent": {"firstLine": 0, "hanging": 0, "start": 0, "left": 720},
                                  "size": 22, "alignment": "both",
                                  "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[12]['properties'][0])
        self.assertEqual([0, 11, {"indent": {"firstLine": 0, "hanging": 0, "start": 0, "left": 1440},
                                  "size": 22, "alignment": "both",
                                  "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[13]['properties'][0])

    def test_example_2(self):
        docx_reader = DOCXParser('examples/example_2.docx')
        lines_with_meta = docx_reader.get_lines_with_meta()
        zero_indent = {"firstLine": 0, "hanging": 0, "start": 0, "left": 0}
        self.assertEqual([0, len(lines_with_meta[0]['text']),
                          {"indent": zero_indent, "size": 32, "alignment": "left",
                           "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[0]['properties'][0])
        self.assertEqual([0, len(lines_with_meta[1]['text']),
                          {"indent": zero_indent, "size": 36, "alignment": "left",
                           "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[1]['properties'][0])
        self.assertEqual([0, len(lines_with_meta[2]['text']),
                          {"indent": zero_indent, "size": 24, "alignment": "left",
                           "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[2]['properties'][0])
        self.assertEqual([0, len(lines_with_meta[3]['text']),
                          {"indent": zero_indent, "size": 28, "alignment": "left",
                           "bold": False, "italic": True, "underlined": False}],
                         lines_with_meta[3]['properties'][0])
        self.assertEqual([0, len(lines_with_meta[8]['text']),
                          {"indent": zero_indent, "size": 21, "alignment": "left",
                           "bold": False, "italic": True, "underlined": False}],
                         lines_with_meta[8]['properties'][0])
        right_answer = [[0, 66, {'alignment': 'left', 'bold': False, 'indent': zero_indent,
                                 'italic': False, 'size': 28, 'underlined': False}],
                        [66, 73, {'alignment': 'left', 'bold': False, 'indent': zero_indent,
                                  'italic': True, 'size': 28, 'underlined': False}],
                        [73, 75, {'alignment': 'left', 'bold': False, 'indent': zero_indent,
                                  'italic': False, 'size': 28, 'underlined': False}],
                        [75, 89, {'alignment': 'left', 'bold': True, 'indent': zero_indent,
                                  'italic': False, 'size': 28, 'underlined': False}],
                        [89, 91, {'alignment': 'left', 'bold': False, 'indent': zero_indent,
                                  'italic': False, 'size': 28, 'underlined': False}],
                        [91, 111, {'alignment': 'left', 'bold': False, 'indent': zero_indent,
                                   'italic': False, 'size': 28, 'underlined': True}],
                        [111, 153, {'alignment': 'left', 'bold': False,'indent': zero_indent,
                                    'italic': False, 'size': 28, 'underlined': False}],
                        [153, 175, {'alignment': 'left', 'bold': False,'indent': zero_indent,
                                    'italic': False, 'size': 40, 'underlined': False}],
                        [175, 183, {'alignment': 'left', 'bold': False, 'indent': zero_indent,
                                    'italic': False, 'size': 28, 'underlined': False}],
                        [183, 199, {'alignment': 'left', 'bold': False, 'indent': zero_indent,
                                    'italic': False, 'size': 22, 'underlined': False}],
                        [199, 244, {'alignment': 'left', 'bold': False, 'indent': zero_indent,
                                    'italic': False, 'size': 28, 'underlined': False}]]
        self.assertEqual(right_answer, lines_with_meta[30]['properties'])
        self.assertEqual([0, len(lines_with_meta[36]['text']),
                          {"indent": zero_indent, "size": 28, "alignment": "right",
                           "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[36]['properties'][0])
        self.assertEqual([0, len(lines_with_meta[37]['text']),
                          {"indent": zero_indent, "size": 28, "alignment": "center",
                           "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[37]['properties'][0])
        self.assertEqual([0, len(lines_with_meta[38]['text']),
                          {"indent": zero_indent, "size": 28, "alignment": "both",
                           "bold": False, "italic": False, "underlined": False}],
                         lines_with_meta[38]['properties'][0])
        self.assertEqual(True, lines_with_meta[39]['properties'][0][2]['bold'])
        self.assertEqual(True, lines_with_meta[40]['properties'][0][2]['italic'])
        self.assertEqual(True, lines_with_meta[41]['properties'][0][2]['underlined'])
        self.assertEqual(True, lines_with_meta[42]['properties'][0][2]['bold'] and
                         lines_with_meta[42]['properties'][0][2]['italic'])
        self.assertEqual(True, lines_with_meta[43]['properties'][0][2]['bold'] and
                         lines_with_meta[43]['properties'][0][2]['italic'] and
                         lines_with_meta[43]['properties'][0][2]['underlined'])
