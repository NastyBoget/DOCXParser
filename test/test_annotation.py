import os
import unittest

from docx_parser.document_parser import DOCXParser

TEST_DIR = '../examples'


class TestAnnotations(unittest.TestCase):

    def test_annotations_libreoffice(self):
        parser = DOCXParser()
        path = os.path.join(TEST_DIR, "annotation_libreoffice_1.docx")
        parser.parse(path)
        result = parser.get_lines_with_meta()

        self.assertEqual('Example document', result[0]['text'])
        self.assertIn(('alignment', 0, 16, 'center'), result[0]['annotations'])
        self.assertIn(('bold', 0, 16, 'True'), result[0]['annotations'])
        self.assertIn(('size', 0, 16, '28.0'), result[0]['annotations'])
        self.assertIn(('style', 0, 16, 'title'), result[0]['annotations'])

        self.assertEqual('Chapter 1', result[1]['text'])
        self.assertIn(('alignment', 0, 9, 'left'), result[1]['annotations'])
        self.assertIn(('bold', 0, 9, 'True'), result[1]['annotations'])
        self.assertIn(('size', 0, 9, '18.0'), result[1]['annotations'])
        self.assertIn(('style', 0, 9, 'heading 1'), result[1]['annotations'])

        self.assertEqual('Here we check simple text', result[2]["text"])
        self.assertIn(('size', 0, 25, '12.0'), result[2]['annotations'])
        self.assertIn(('style', 0, 25, 'body text'), result[2]['annotations'])

        self.assertEqual('Chapter 1.1', result[3]['text'])
        self.assertIn(('bold', 0, 11, 'True'), result[3]['annotations'])
        self.assertIn(('size', 0, 11, '16.0'), result[3]['annotations'])
        self.assertIn(('style', 0, 11, 'heading 2'), result[3]['annotations'])

        self.assertEqual('1.\tHere', result[4]['text'])
        self.assertIn(('size', 0, 7, '12.0'), result[4]['annotations'])
        self.assertIn(('style', 0, 7, 'body text'), result[4]['annotations'])

        self.assertEqual('Chapter 1.1.1', result[8]['text'])
        self.assertIn(('bold', 0, 13, 'True'), result[8]['annotations'])
        self.assertIn(('size', 0, 13, '14.0'), result[8]['annotations'])
        self.assertIn(('style', 0, 13, 'heading 3'), result[8]['annotations'])

        self.assertEqual('HERE WE CHECK CAPS LETTERS', result[9]['text'])

        self.assertEqual('Here we check custom styles', result[11]['text'])
        self.assertIn(('alignment', 0, 27, 'center'), result[11]['annotations'])
        self.assertIn(('italic', 0, 27, 'True'), result[11]['annotations'])
        self.assertIn(('size', 0, 27, '13.0'), result[11]['annotations'])
        self.assertIn(('style', 0, 27, 'custom style'), result[11]['annotations'])

        self.assertEqual('−\tHere we check custom ', result[12]['text'])
        self.assertIn(('italic', 0, 23, 'True'), result[12]['annotations'])
        self.assertIn(('style', 0, 23, 'custom style with numbering'), result[12]['annotations'])

        self.assertEqual('Here we check bold, italic, underlined, large font and small font.', result[15]['text'])
        self.assertIn(('bold', 14, 18, 'True'), result[15]['annotations'])
        self.assertIn(('italic', 20, 26, 'True'), result[15]['annotations'])
        self.assertIn(('underlined', 28, 38, 'True'), result[15]['annotations'])
        self.assertIn(('size', 0, 40, '12.0'), result[15]['annotations'])
        self.assertIn(('size', 40, 50, '18.0'), result[15]['annotations'])
        self.assertIn(('size', 50, 55, '12.0'), result[15]['annotations'])
        self.assertIn(('size', 55, 65, '8.0'), result[15]['annotations'])
        self.assertIn(('size', 65, 66, '12.0'), result[15]['annotations'])

        self.assertEqual('Center justification', result[16]['text'])
        self.assertIn(('alignment', 0, 20, 'center'), result[16]['annotations'])

        self.assertEqual('Both justification', result[17]['text'])
        self.assertIn(('alignment', 0, 18, 'both'), result[17]['annotations'])

        self.assertEqual('Right justification', result[18]['text'])
        self.assertIn(('alignment', 0, 19, 'right'), result[18]['annotations'])

        self.assertEqual('⎝\tHere', result[20]['text'])

        path = os.path.join(TEST_DIR, "annotation_libreoffice_2.docx")
        parser.parse(path)
        result = parser.get_lines_with_meta()

        self.assertEqual('Техническое задание\nна оказание услуг по созданию системы защиты персональных данных ',
                         result[0]['text'])
        self.assertIn(('alignment', 0, 85, 'center'), result[0]['annotations'])
        self.assertIn(('bold', 0, 85, 'True'), result[0]['annotations'])
        self.assertIn(('size', 0, 85, '12.0'), result[0]['annotations'])
        self.assertIn(('style', 0, 85, 'normal'), result[0]['annotations'])

        self.assertEqual('1.\tНаименование оказываемых услуг.', result[3]['text'])
        self.assertIn(('alignment', 0, 34, 'center'), result[3]['annotations'])
        self.assertIn(('bold', 0, 34, 'True'), result[3]['annotations'])
        self.assertIn(('style', 0, 34, 'list paragraph'), result[3]['annotations'])

        self.assertEqual('Услуги по созданию системы защиты персональных данных и аттестации автоматизированных '
                         'рабочих мест в администрации Пушкинского муниципального района Московской области '
                         '(далее – Заказчик).', result[4]['text'])
        self.assertIn(('alignment', 0, 187, 'both'), result[4]['annotations'])
        self.assertNotIn(('bold', 0, 187, 'True'), result[4]['annotations'])

        self.assertEqual('7. Общие требования к оказанию услуг, требования к их качеству, в том числе к '
                         'техническим характеристикам поставляемых средств защиты информации.', result[6]['text'])
        self.assertIn(('bold', 0, 145, 'True'), result[6]['annotations'])

        # TODO handle such lists more correctly
        self.assertEqual('7.\tУслуги по обновлению системы защиты информации должны быть оказаны в соответствии с '
                         'требованиями и рекомендациями следующих нормативных документов:', result[7]['text'])
        self.assertIn(('style', 0, 150, 'list paragraph'), result[7]['annotations'])

        self.assertEqual('⎯\tФедеральный закон от 27 июля 2006 г. № 149-ФЗ "Об информации, '
                         'информационных технологиях и о защите информации".', result[8]['text'])
        self.assertIn(('style', 0, 114, 'list paragraph'), result[8]['annotations'])

        self.assertEqual('7.1.\tДоработка проектов организационно-распорядительной документации.', result[9]['text'])
        self.assertEqual('-\tАнализ процесса обработки персональных данных.', result[11]['text'])
        self.assertEqual('• управление заявками пользователей (заявки на обслуживание и техподдержку);',
                         result[13]['text'])
        self.assertEqual('7.2.\tТребования к качественным и техническим характеристикам программного обеспечения, '
                         'реализующего функции средства анализа защищенности:', result[14]['text'])
        self.assertEqual('⎯\tАнализ и классификацию уязвимостей на 32 узлах защищаемой сети.', result[16]['text'])

    def test_annotations_pages(self):
        parser = DOCXParser()
        path = os.path.join(TEST_DIR, "annotation_pages_1.docx")
        parser.parse(path)
        result = parser.get_lines_with_meta()

        self.assertEqual('Plain text', result[0]['text'])
        self.assertIn(('size', 0, 10, '11.0'), result[0]['annotations'])

        self.assertEqual('Italic text', result[1]['text'])
        self.assertIn(('italic', 0, 11, 'True'), result[1]['annotations'])
        self.assertIn(('size', 0, 11, '12.0'), result[1]['annotations'])

        self.assertEqual('Bold text', result[2]['text'])
        self.assertIn(('bold', 0, 9, 'True'), result[2]['annotations'])

        self.assertEqual('Underlined text', result[3]['text'])
        self.assertIn(('underlined', 0, 15, 'True'), result[3]['annotations'])

        self.assertEqual('Italic nonitalic', result[4]['text'])
        self.assertIn(('italic', 0, 6, 'True'), result[4]['annotations'])
        self.assertIn(('size', 0, 16, '13.0'), result[4]['annotations'])

        self.assertEqual('Nonbold bold', result[5]['text'])
        self.assertIn(('bold', 8, 12, 'True'), result[5]['annotations'])
        self.assertIn(('size', 0, 12, '14.0'), result[5]['annotations'])

        self.assertEqual('Bold boldUnderlined', result[6]['text'])
        self.assertIn(('bold', 0, 19, 'True'), result[6]['annotations'])
        self.assertIn(('underlined', 5, 19, 'True'), result[6]['annotations'])
        self.assertIn(('size', 0, 19, '11.0'), result[6]['annotations'])

        self.assertEqual('Left text', result[7]['text'])
        self.assertIn(('alignment', 0, 9, 'left'), result[7]['annotations'])

        self.assertEqual('Centered text', result[8]['text'])
        self.assertIn(('alignment', 0, 13, 'center'), result[8]['annotations'])

        self.assertEqual('Right text', result[9]['text'])
        self.assertIn(('alignment', 0, 10, 'right'), result[9]['annotations'])

        self.assertEqual('Text aligned to both borders', result[10]['text'])
        self.assertIn(('alignment', 0, 28, 'both'), result[10]['annotations'])

        self.assertEqual('Zero indent', result[11]['text'])
        self.assertIn(('indentation', 0, 11, '0'), result[11]['annotations'])

        self.assertEqual('One indent', result[12]['text'])
        self.assertIn(('indentation', 0, 10, '720'), result[12]['annotations'])

        self.assertEqual('Two indents', result[13]['text'])
        self.assertIn(('indentation', 0, 11, '1440'), result[13]['annotations'])

        path = os.path.join(TEST_DIR, "annotation_pages_2.docx")
        parser.parse(path)
        result = parser.get_lines_with_meta()

        self.assertEqual('The first line', result[0]['text'])
        self.assertIn(('size', 0, 14, '15.0'), result[0]['annotations'])

        self.assertEqual('The second line', result[1]['text'])
        self.assertIn(('size', 0, 15, '12.0'), result[1]['annotations'])

        self.assertEqual('The third line', result[2]['text'])
        self.assertIn(('size', 0, 14, '13.0'), result[2]['annotations'])

        self.assertEqual('11 line', result[8]['text'])
        self.assertIn(('bold', 0, 7, 'True'), result[8]['annotations'])

        self.assertEqual('12 line', result[9]['text'])
        self.assertIn(('italic', 0, 7, 'True'), result[9]['annotations'])

        self.assertEqual('13 line', result[10]['text'])
        self.assertIn(('italic', 0, 7, 'True'), result[10]['annotations'])
        self.assertIn(('underlined', 0, 7, 'True'), result[10]['annotations'])

        self.assertEqual('15 line', result[12]['text'])
        self.assertIn(('alignment', 0, 7, 'center'), result[12]['annotations'])

        self.assertEqual('16 line', result[13]['text'])
        self.assertIn(('alignment', 0, 7, 'right'), result[13]['annotations'])

        self.assertEqual('18 line', result[15]['text'])
        self.assertIn(('indentation', 0, 7, '720'), result[15]['annotations'])

        self.assertEqual('19 line', result[16]['text'])
        self.assertIn(('indentation', 0, 7, '1440'), result[16]['annotations'])

        self.assertEqual('•\t21 line', result[18]['text'])
        self.assertIn(('italic', 5, 9, 'True'), result[18]['annotations'])

        self.assertEqual('•\t22 line', result[19]['text'])
        self.assertIn(('indentation', 0, 9, '245'), result[19]['annotations'])

        self.assertEqual('1.\t23 line', result[20]['text'])
        self.assertIn(('indentation', 0, 10, '360'), result[20]['annotations'])

        self.assertEqual('2.\t24 line', result[21]['text'])
        self.assertIn(('indentation', 0, 10, '643'), result[21]['annotations'])
        self.assertIn(('bold', 6, 10, 'True'), result[21]['annotations'])

        self.assertEqual('3)\t25 строка', result[22]['text'])
        self.assertEqual('4)\t26 строка', result[23]['text'])

    def test_annotations_word(self):
        parser = DOCXParser()
        path = os.path.join(TEST_DIR, "annotation_word_1.docx")
        parser.parse(path)
        result = parser.get_lines_with_meta()

        self.assertEqual('Это заголовок первого уровня', result[0]['text'])
        self.assertIn(('size', 0, 28, '16.0'), result[0]['annotations'])
        self.assertIn(('style', 0, 28, 'heading 1'), result[0]['annotations'])

        self.assertEqual('Это заголовок четвёртого уровня', result[3]['text'])
        self.assertIn(('italic', 0, 31, 'True'), result[3]['annotations'])
        self.assertIn(('size', 0, 31, '14.0'), result[3]['annotations'])
        self.assertIn(('style', 0, 31, 'heading 4'), result[3]['annotations'])

        self.assertEqual('Это заголовок седьмого уровня', result[6]['text'])
        self.assertIn(('italic', 0, 29, 'True'), result[6]['annotations'])
        self.assertIn(('style', 0, 29, 'heading 7'), result[6]['annotations'])

        self.assertEqual('Это заголовок девятого уровня', result[8]['text'])
        self.assertIn(('italic', 0, 29, 'True'), result[8]['annotations'])
        self.assertIn(('size', 0, 29, '10.5'), result[8]['annotations'])
        self.assertIn(('style', 0, 29, 'heading 9'), result[8]['annotations'])

        self.assertEqual('Это обычный текст', result[9]['text'])
        self.assertIn(('size', 0, 17, '14.0'), result[9]['annotations'])

        self.assertEqual('•\tПервый элемент маркированного списка', result[10]['text'])
        self.assertIn(('indentation', 0, 38, '720'), result[10]['annotations'])
        self.assertIn(('size', 0, 38, '14.0'), result[10]['annotations'])
        self.assertIn(('style', 0, 38, 'list paragraph'), result[10]['annotations'])

        self.assertEqual('1.\tПервый элемент нумерованного списка', result[13]['text'])
        self.assertEqual('1.\tПервый элемент сложного нумерованного списка', result[16]['text'])
        self.assertEqual('1.1.\tПервый элемент первого элемента списка', result[17]['text'])
        self.assertEqual('3.2.1.\tПервый элемент второго элемента третьего элемента списка', result[23]['text'])
        self.assertEqual('•\tПервый элемент второго маркированного списка', result[26]['text'])
        self.assertEqual('a)\tПервый элемент буквенного нумерованного списка', result[28]['text'])

        self.assertEqual('Обычный параграф, внутри которого присутствует вcякая дичь в виде курсива, жирного шрифта, '
                         'подчёркнутого шрифта, а также выделенный текст другим цветом, шрифт большего размера, шрифт '
                         'меньшего размера, и, конечно же, шрифт с другим font-name’ом.', result[30]['text'])
        self.assertIn(('italic', 66, 73, 'True'), result[30]['annotations'])
        self.assertIn(('bold', 75, 89, 'True'), result[30]['annotations'])
        self.assertIn(('underlined', 91, 111, 'True'), result[30]['annotations'])
        self.assertIn(('size', 0, 153, '14.0'), result[30]['annotations'])
        self.assertIn(('size', 153, 175, '20.0'), result[30]['annotations'])
        self.assertIn(('size', 175, 183, '14.0'), result[30]['annotations'])
        self.assertIn(('size', 183, 199, '11.0'), result[30]['annotations'])
        self.assertIn(('size', 199, 244, '14.0'), result[30]['annotations'])

        self.assertEqual('5.\tВнезапное продолжение того сложного списка, пункт 5', result[31]['text'])
        self.assertEqual('•\tМаркированный список из одного элемента', result[33]['text'])
        self.assertEqual('7.\tЕщё один пункт сложного списка', result[34]['text'])

        self.assertEqual('Обычный текст с выравниванием по левому краю', result[35]['text'])
        self.assertIn(('alignment', 0, 44, 'left'), result[35]['annotations'])

        self.assertEqual('Обычный текст с выравниванием по правому краю', result[36]['text'])
        self.assertIn(('alignment', 0, 45, 'right'), result[36]['annotations'])

        self.assertEqual('Обычный текст с выравниванием по центру', result[37]['text'])
        self.assertIn(('alignment', 0, 39, 'center'), result[37]['annotations'])

        self.assertEqual('Обычный текст, который мы решили растянуть по всей ширине страницы, чтобы проверить, как '
                         'оно будет выглядеть, а для этого приходится писать этот длинный текст.', result[38]['text'])
        self.assertIn(('alignment', 0, 159, 'both'), result[38]['annotations'])

        self.assertEqual('Этот параграф весь жирный', result[39]['text'])
        self.assertIn(('bold', 0, 25, 'True'), result[39]['annotations'])

        self.assertEqual('Этот параграф весь курсивный', result[40]['text'])
        self.assertIn(('italic', 0, 28, 'True'), result[40]['annotations'])

        self.assertEqual('Этот параграф весь подчёркнутый', result[41]['text'])
        self.assertIn(('underlined', 0, 31, 'True'), result[41]['annotations'])

        self.assertEqual('Этот параграф и жирный и курсивный', result[42]['text'])
        self.assertIn(('bold', 0, 34, 'True'), result[42]['annotations'])
        self.assertIn(('italic', 0, 34, 'True'), result[42]['annotations'])

        self.assertEqual('Этот параграф и курсивный, и жирный и подчёркнутый', result[43]['text'])
        self.assertIn(('bold', 0, 50, 'True'), result[43]['annotations'])
        self.assertIn(('italic', 0, 50, 'True'), result[43]['annotations'])
        self.assertIn(('underlined', 0, 50, 'True'), result[43]['annotations'])

        path = os.path.join(TEST_DIR, "annotation_word_2.docx")
        parser.parse(path)
        result = parser.get_lines_with_meta()

        self.assertEqual('Header 1', result[0]['text'])
        self.assertIn(('size', 0, 8, '16.0'), result[0]['annotations'])
        self.assertIn(('style', 0, 8, 'heading 1'), result[0]['annotations'])

        self.assertEqual('Header 3', result[1]['text'])
        self.assertIn(('size', 0, 8, '12.0'), result[1]['annotations'])
        self.assertIn(('style', 0, 8, 'heading 3'), result[1]['annotations'])

        self.assertEqual('Simple text', result[6]['text'])
        self.assertIn(('alignment', 0, 11, 'center'), result[6]['annotations'])

        self.assertEqual('1.\tBullet list point 1', result[7]['text'])
        self.assertIn(('style', 0, 22, 'list paragraph'), result[7]['annotations'])

        self.assertEqual('Some simple text again', result[11]['text'])
        self.assertIn(('alignment', 0, 22, 'right'), result[11]['annotations'])

        self.assertEqual('Start of a little table', result[20]['text'])
        self.assertIn(('size', 0, 23, '18.0'), result[20]['annotations'])
        self.assertIn(('style', 0, 23, 'heading 2'), result[20]['annotations'])

        self.assertEqual('•\tBullet list 2 point 1', result[23]['text'])
        self.assertIn(('indentation', 0, 23, '720'), result[23]['annotations'])

        self.assertEqual('Test hard lists:', result[27]['text'])
        self.assertIn(('size', 0, 5, '14.0'), result[27]['annotations'])
        self.assertIn(('size', 5, 9, '18.0'), result[27]['annotations'])
        self.assertIn(('size', 9, 16, '14.0'), result[27]['annotations'])

        self.assertEqual('1. First item', result[28]['text'])

        self.assertEqual('Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt '
                         'ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco '
                         'laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in '
                         'voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat '
                         'cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
                         result[40]['text'])
        self.assertIn(('alignment', 0, 446, 'both'), result[40]['annotations'])
        self.assertIn(('size', 0, 197, '14.0'), result[40]['annotations'])
        self.assertIn(('size', 197, 221, '18.0'), result[40]['annotations'])
        self.assertIn(('bold', 243, 325, 'True'), result[40]['annotations'])
        self.assertIn(('size', 221, 446, '14.0'), result[40]['annotations'])

        self.assertEqual('Test test test', result[41]['text'])
        self.assertIn(('size', 0, 14, '16.0'), result[41]['annotations'])
        self.assertIn(('style', 0, 14, 'heading 1'), result[41]['annotations'])

        self.assertEqual('Blab la bla', result[42]['text'])
        self.assertIn(('size', 0, 11, '14.0'), result[42]['annotations'])

        path = os.path.join(TEST_DIR, "annotation_word_3.docx")
        parser.parse(path)
        result = parser.get_lines_with_meta()

        self.assertEqual('Договор № ____', result[0]['text'])
        self.assertIn(('alignment', 0, 14, 'center'), result[0]['annotations'])
        self.assertIn(('bold', 0, 14, 'True'), result[0]['annotations'])

        self.assertEqual('Общество с ограниченной ответственностью «Объединенная дирекция по управлению активами и '
                         'сервисами Центра разработки и коммерциализации новых технологий (инновационного центра '
                         '«Сколково»)» (ООО «ОДАС Сколково»), именуемое в дальнейшем «Заказчик», в лице Директора '
                         'Дирекции по эксплуатации объектов недвижимости  Троценко Дениса Сергеевича, действующего '
                         'на основании Доверенности № 37 от 10.07.2015 г., с одной стороны, и', result[3]['text'])
        self.assertIn(('alignment', 0, 420, 'both'), result[3]['annotations'])
        self.assertIn(('bold', 0, 210, 'True'), result[3]['annotations'])
        self.assertIn(('bold', 236, 244, 'True'), result[3]['annotations'])

        self.assertEqual(' ______________________________________(__)_, именуемое в дальнейшем «Исполнитель», '
                         'в лице __________________________________, действующего на основании _______________, '
                         'с другой стороны, в дальнейшем совместно именуемые «Стороны», а по отдельности «Сторона», '
                         'заключили настоящий договор (далее – «Договор») о нижеследующем.', result[4]['text'])
        self.assertIn(('bold', 1, 46, 'True'), result[4]['annotations'])
        self.assertIn(('bold', 70, 81, 'True'), result[4]['annotations'])

        self.assertEqual('Статья 1. Термины и определения', result[5]['text'])
        self.assertIn(('bold', 0, 31, 'True'), result[5]['annotations'])

        self.assertEqual('1.\t«АВР» – аварийно-восстановительные работы, связанные с оперативным реагированием '
                         'Исполнителя и устранением последствий нештатных (аварийных) ситуаций при эксплуатации '
                         'Инженерных систем.', result[7]['text'])
        self.assertIn(('bold', 0, 9, 'True'), result[7]['annotations'])

        self.assertEqual('Статья 2. Предмет Договора', result[8]['text'])
        self.assertIn(('bold', 0, 26, 'True'), result[8]['annotations'])

        self.assertEqual('1.\tВ соответствии с настоящим Договором, Заказчик поручает, а Исполнитель принимает на '
                         'себя обязательства своевременно и в полном объеме выполнять комплекс работ и услуг по '
                         'содержанию объектов (зданий и строений), сервисному и техническому обслуживанию комплекса '
                         'объектов инженерной инфраструктуры (далее – «Работы»), в соответствии с условиями настоящего '
                         'Договора и Приложений к нему, включая:', result[9]['text'])
        self.assertIn(('bold', 147, 298, 'True'), result[9]['annotations'])

        self.assertEqual('- Техническую эксплуатацию Инженерных систем;', result[10]['text'])
