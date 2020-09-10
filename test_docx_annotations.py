import unittest
from document_parser import DOCXParser


class TestDocxAnnotations(unittest.TestCase):

    def test_example_1(self):
        docx_reader = DOCXParser('examples/example_1.docx')
        lines_with_meta = docx_reader.get_lines_with_meta()
        # bold, italic, underlined
        self.assertEqual([(0, 10, 'style:Body A')], lines_with_meta[0]['annotations'])
        self.assertEqual([(0, 11, "italic"), (0, 11, 'style:Body A')], lines_with_meta[1]['annotations'])
        self.assertEqual([(0, 9, "bold"), (0, 9, 'style:Body A')], lines_with_meta[2]['annotations'])
        self.assertEqual([(0, 15, "underlined"), (0, 15, 'style:Body A')], lines_with_meta[3]['annotations'])
        self.assertEqual([(0, 6, "italic"), (0, 16, 'style:Body A')], lines_with_meta[4]['annotations'])
        self.assertEqual([(8, 12, "bold"), (0, 12, 'style:Body A')], lines_with_meta[5]['annotations'])
        self.assertEqual([(0, 19, "bold"), (5, 19, "underlined"), (0, 19, 'style:Body A')],
                         lines_with_meta[6]['annotations'])

        # alignment
        self.assertEqual("left", lines_with_meta[8]['alignment'])
        self.assertEqual("center", lines_with_meta[9]['alignment'])
        self.assertEqual("right", lines_with_meta[10]['alignment'])
        self.assertEqual("both", lines_with_meta[11]['alignment'])
        # indent
        self.assertEqual({"firstLine": 0, "hanging": 0, "start": 0, "left": 0}, lines_with_meta[12]['indent'])
        self.assertEqual({"firstLine": 0, "hanging": 0, "start": 0, "left": 720}, lines_with_meta[13]['indent'])
        self.assertEqual({"firstLine": 0, "hanging": 0, "start": 0, "left": 1440}, lines_with_meta[14]['indent'])

    def test_example_2(self):
        docx_reader = DOCXParser('examples/example_2.docx')
        lines_with_meta = docx_reader.get_lines_with_meta()
        self.assertEqual([(0, len(lines_with_meta[3]['text']), "italic"),
                          (0, len(lines_with_meta[3]['text']), 'style:heading 4')], lines_with_meta[3]['annotations'])
        self.assertEqual([(0, len(lines_with_meta[8]['text']), "italic"),
                          (0, len(lines_with_meta[8]['text']), 'style:heading 9')], lines_with_meta[8]['annotations'])

        self.assertEqual([(66, 73, "italic"), (75, 89, "bold"), (91, 111, 'underlined')],
                         lines_with_meta[35]['annotations'])

        self.assertEqual("right", lines_with_meta[43]['alignment'])
        self.assertEqual("center", lines_with_meta[44]['alignment'])
        self.assertEqual("both", lines_with_meta[45]['alignment'])

        self.assertEqual([(0, len(lines_with_meta[47]['text']), "bold")], lines_with_meta[47]['annotations'])
        self.assertEqual([(0, len(lines_with_meta[48]['text']), "italic")], lines_with_meta[48]['annotations'])
        self.assertEqual([(0, len(lines_with_meta[49]['text']), "underlined")], lines_with_meta[49]['annotations'])
        self.assertEqual([(0, len(lines_with_meta[50]['text']), "bold"),
                          (0, len(lines_with_meta[50]['text']), "italic")], lines_with_meta[50]['annotations'])
        self.assertEqual([(0, len(lines_with_meta[51]['text']), "bold"),
                          (0, len(lines_with_meta[51]['text']), "italic"),
                          (0, len(lines_with_meta[51]['text']), "underlined")], lines_with_meta[51]['annotations'])
