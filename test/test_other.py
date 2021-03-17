import os
import unittest

from docx_parser.document_parser import DOCXParser

TEST_DIR = '../examples'


class TestOther(unittest.TestCase):

    def test_caps(self):
        parser = DOCXParser()
        path = os.path.join(TEST_DIR, "caps_1.docx")
        parser.parse(path)
        result = parser.get_lines_with_meta()
        self.assertEqual('ШИЖМАШ МОГАЙ ЛИЕШ ГЫН?\t', result[0]["text"])
        self.assertEqual('АНАСТАСИЯ АЙГУЗИНА', result[1]["text"])
        path = os.path.join(TEST_DIR, "caps_2.docx")
        parser.parse(path)
        result = parser.get_lines_with_meta()
        self.assertEqual('И. Одар "Таргылтыш"', result[0]["text"])
        self.assertEqual('I глава', result[1]["text"])

    def test_without_numbering(self):
        parser = DOCXParser()
        path = os.path.join(TEST_DIR, "without_numbering.docx")
        try:
            parser.parse(path)
            result = parser.get_lines_with_meta()
        except AttributeError:
            result = None
        self.assertTrue(result is not None)
