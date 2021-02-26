import os
import unittest
from typing import List

from document_parser import DOCXParser

TEST_DIR = '../examples'


class TestStyles(unittest.TestCase):

    def __test_content(self,
                       result: List[dict]):
        self.assertEqual('Документ предоставлен КонсультантПлюс\n', result[0]["text"])
        self.assertIn(('style', 0, 38, 'consplustitlepage'), result[0]["annotations"])
        self.assertNotIn(('bold', 0, 38, 'True'), result[0]["annotations"])
        self.assertEqual('РОССИЙСКАЯ ФЕДЕРАЦИЯ', result[1]["text"])
        self.assertIn(('style', 0, 20, 'consplustitle'), result[1]["annotations"])
        self.assertIn(('bold', 0, 20, 'True'), result[1]["annotations"])
        self.assertEqual('ФЕДЕРАЛЬНЫЙ ЗАКОН', result[2]["text"])
        self.assertIn(('style', 0, 17, 'consplustitle'), result[2]["annotations"])
        self.assertIn(('bold', 0, 17, 'True'), result[2]["annotations"])
        self.assertEqual('О ПОРЯДКЕ РАССМОТРЕНИЯ ОБРАЩЕНИЙ', result[3]["text"])
        self.assertIn(('style', 0, 32, 'consplustitle'), result[3]["annotations"])
        self.assertIn(('bold', 0, 32, 'True'), result[3]["annotations"])
        self.assertEqual('ГРАЖДАН РОССИЙСКОЙ ФЕДЕРАЦИИ', result[4]["text"])
        self.assertIn(('style', 0, 28, 'consplustitle'), result[4]["annotations"])
        self.assertIn(('bold', 0, 28, 'True'), result[4]["annotations"])
        self.assertEqual('Принят', result[5]["text"])
        self.assertIn(('style', 0, 6, 'consplusnormal'), result[5]["annotations"])
        self.assertNotIn(('bold', 0, 6, 'True'), result[5]["annotations"])
        self.assertEqual('Государственной Думой', result[6]["text"])
        self.assertIn(('style', 0, 21, 'consplusnormal'), result[6]["annotations"])
        self.assertNotIn(('bold', 0, 21, 'True'), result[6]["annotations"])
        self.assertEqual('21 апреля 2006 года', result[7]["text"])
        self.assertIn(('style', 0, 19, 'consplusnormal'), result[7]["annotations"])
        self.assertNotIn(('bold', 0, 19, 'True'), result[7]["annotations"])

        self.assertEqual('Статья 1. Сфера применения настоящего Федерального закона', result[11]["text"])
        self.assertIn(('style', 0, 57, 'consplustitle'), result[11]["annotations"])
        self.assertIn(('bold', 0, 57, 'True'), result[11]["annotations"])
        self.assertEqual('1. Настоящим Федеральным законом регулируются правоотношения, '
                         'связанные с реализацией гражданином Российской Федерации (далее также - гражданин) '
                         'закрепленного за ним Конституцией Российской Федерации права на обращение в '
                         'государственные органы и органы местного самоуправления, а также устанавливается порядок '
                         'рассмотрения обращений граждан государственными органами, органами местного самоуправления '
                         'и должностными лицами.', result[12]["text"])
        self.assertIn(('style', 0, 423, 'consplusnormal'), result[12]["annotations"])
        self.assertNotIn(('bold', 0, 423, 'True'), result[12]["annotations"])

        self.assertEqual('(часть 4 введена Федеральным законом от 07.05.2013 N 80-ФЗ)', result[16]["text"])
        self.assertIn(('style', 0, 59, 'consplusnormal'), result[16]["annotations"])
        self.assertNotIn(('bold', 0, 59, 'True'), result[16]["annotations"])

    def test_style_libreoffice(self):
        parser = DOCXParser()
        path = os.path.join(TEST_DIR, "with_style_libreoffice.docx")
        parser.parse(path)
        result = parser.get_lines_with_meta()
        self.__test_content(result)

    def test_style_pages(self):
        parser = DOCXParser()
        path = os.path.join(TEST_DIR, "with_style_pages.docx")
        parser.parse(path)
        result = parser.get_lines_with_meta()
        self.__test_content(result)
