import os
import re
import tempfile
import time
import zipfile
from abc import abstractmethod, ABC
from collections import namedtuple
from typing import Iterator, Optional, Dict, Iterable
from typing import List

import numpy as np
from PIL import Image
from bs4 import BeautifulSoup
from pdf2image import convert_from_path

from docx_parser.document_parser import DOCXParser

PairedPdf = namedtuple("PairedPdf", ["many_color_pdf", "two_color_pdf", "many_colors", "two_colors"])


class AbstractDocxImagesCreator(ABC):

    def __init__(self,
                 path2docs: str):
        self.path2docs = path2docs
        self.docx_reader = DOCXParser()
        self.color_step = 16
        self.first_color = 15
        self.base_color = 0
        self.base_color_step = 1
        self.many_colors_file_name = 'many_colors_doc'
        self.two_colors_file_name = 'two_colors_doc'

    def create_images(self,
                      path: str) -> Iterator[Optional[Image.Image]]:
        """
        The algorithm if as follows:
        1 create two pdf: the first with bboxes around paragraph (each of different color) and the second with
        bboxes of two colors.
        2 We read images from both pdf (one page by one) and subtracting first image from the second (we get image with
        nonzero pixels on bboxes only)
        3 we clear bboxes from first image
        4 and create one image per bbox and save in tmp dir
        5 and finally we return image with bboxes in the proper order
        @param path: path to docx document
        @return: sequence of Images
        """

        # here we get half processing docx document (with raw xml)
        self.docx_reader.parse(os.path.join(self.path2docs, path))
        with zipfile.ZipFile(os.path.join(self.path2docs, path)) as d:
            with tempfile.TemporaryDirectory() as tmp_dir:
                pdfs = self.__create_pair_pdfs(docx_archive=d, tmp_dir=tmp_dir)
                # create image with bbox
                yield from self._create_images_from_pdf(pdfs=pdfs, tmp_dir=tmp_dir)

    @abstractmethod
    def _create_images_from_pdf(self, pdfs: PairedPdf, tmp_dir: str) -> Iterable[Image.Image]:
        """
        we take two paired pdfs with bboxes and create images from them. Then we return images according to
        page order
        @param pdfs: tuple with path to 2 pdfs and info about used colors
        @param tmp_dir: path where we save intermediate images
        @return:
        """
        pass

    def __create_pair_pdfs(self, docx_archive: zipfile.ZipFile, tmp_dir: str) -> PairedPdf:
        """
        here we create two paired pdfs, we modify docx xml (drow bbox around paragraph) and create pdf, based on this
        modified docx. We create pdf with multi colors and with two colors
        @param docx_archive: opened docx document (docx is a zip archive)
        @param tmp_dir: directory where we save intermediate results
        @return:
        """
        docx_archive.extractall(tmp_dir)
        namelist = docx_archive.namelist()
        document_bs = self.docx_reader.get_document_bs
        paragraph_list = [par for par in self.docx_reader.get_paragraph_xml_list]
        # create docx file with bboxes of different colors
        used_many_colors = self.__draw_bboxes(paragraph_list=paragraph_list, many_colors=True)
        # document_bs was changed implicitly
        text = re.sub("w:pbdr", "w:pBdr", str(document_bs))
        text = re.sub("w:ppr", "w:pPr", text)
        many_colors_pdf = self.__create_pdf_from_docx(tmp_dir, self.many_colors_file_name, namelist, text)
        # clear document_bs from border tags
        border_tags = document_bs.find_all('w:pbdr')
        for tag in border_tags:
            tag.decompose()
        # create docx file with bboxes of two interleaving colors
        used_two_colors = self.__draw_bboxes(paragraph_list=paragraph_list, many_colors=False)
        # document_bs was changed implicitly
        text = re.sub("pbdr", "pBdr", str(document_bs))
        text = re.sub("w:ppr", "w:pPr", text)
        two_colors_pdf = self.__create_pdf_from_docx(tmp_dir, self.two_colors_file_name, namelist, text)
        return PairedPdf(many_colors_pdf, two_colors_pdf, used_many_colors, used_two_colors)

    def __draw_bboxes(self,
                      paragraph_list: List[BeautifulSoup],
                      many_colors: bool) -> Dict[str, int]:
        """
        draw bbox in docx document around each paragraph
        @param paragraph_list:
        @param many_colors:
        @return:
        """
        if many_colors:
            decimal_color = self.first_color
        else:
            decimal_color = self.base_color
        used_colors = {}
        # draw bboxes using different colors
        # if many_colors == False we draw bboxes using
        # only two interleaving colors for correct drawing bboxes in docx
        lines = self.docx_reader.get_lines_with_meta()
        for paragraph, line in zip(paragraph_list, lines):
            color = self._color_from_decimal(decimal_color)
            used_colors[line["uid"]] = decimal_color
            self.__insert_border(paragraph, color)
            if many_colors:
                decimal_color += self.color_step
            else:
                if decimal_color == self.base_color:
                    decimal_color += self.base_color_step
                else:
                    decimal_color -= self.base_color_step
        return used_colors

    @staticmethod
    def _color_from_decimal(decimal_color: int) -> str:
        color = hex(decimal_color)[2:]
        if len(color) < 6:
            color = '0' * (6 - len(color)) + color
        return color

    @staticmethod
    def __create_pdf_from_docx(tmp_dir: str,
                               doc_name: str,
                               namelist: List[str],
                               doc_text: str) -> str:
        with open('{}/word/document.xml'.format(tmp_dir), 'w') as f:
            f.write(doc_text)
        docx_path = "{}/{}.docx".format(tmp_dir, doc_name)
        with zipfile.ZipFile(docx_path, mode='w') as new_d:
            for filename in namelist:
                new_d.write('{}/{}'.format(tmp_dir, filename), arcname=filename)
        # create pdf file with bbox
        pdf_name = AbstractDocxImagesCreator.__docx2pdf(tmp_dir, docx_path)
        os.remove(docx_path)
        return pdf_name

    @staticmethod
    def __await_for_conversion(filename: str) -> None:
        timeout = 10
        period_checking = 0.05
        t = 0
        while (not os.path.isfile(filename)) and (t < timeout):
            time.sleep(period_checking)
            t += period_checking

            if t >= timeout:
                raise Exception("fail with {filename}".format(filename=filename))

    @staticmethod
    def __docx2pdf(out_dir: str,
                   path: str) -> str:
        os.system("/Applications/LibreOffice.app/Contents/MacOS/soffice --headless"
                  " --convert-to pdf {} --outdir {}".format(path, out_dir))
        out_file = '{}/{}pdf'.format(out_dir, os.path.split(path)[-1][:-4])
        AbstractDocxImagesCreator.__await_for_conversion(out_file)
        return out_file

    @staticmethod
    def __insert_border(bs_tree: Optional[BeautifulSoup],
                        color: str) -> None:
        if bs_tree is None:
            return
        border_str = '<w:pBdr><w:top w:val="single" ' \
                     'w:color="{color}" w:sz="8" w:space="0" ' \
                     'w:shadow="0" w:frame="0"/><w:left w:val="single" ' \
                     'w:color="{color}" w:sz="8" w:space="0" ' \
                     'w:shadow="0" w:frame="0"/><w:bottom w:val="single" ' \
                     'w:color="{color}" w:sz="8" w:space="0" w:shadow="0" ' \
                     'w:frame="0"/><w:right w:val="single" w:color="{color}" ' \
                     'w:sz="8" w:space="0" w:shadow="0" w:frame="0"/></w:pBdr>'.format(color=color)
        border_bs = BeautifulSoup(border_str, 'lxml').body.contents[0]
        if bs_tree.pPr:
            bs_tree.pPr.insert(1, border_bs)
        else:
            border_bs = BeautifulSoup('<w:pPr>' + border_str + '</w:pPr>', 'lxml').body.contents[0]
            bs_tree.insert(0, border_bs)

    @staticmethod
    def _split_pdf2image(path: str) -> Iterator[np.ndarray]:
        page_num = 1
        images = None
        while images is None or len(images) > 0:
            images = convert_from_path(path, first_page=page_num, last_page=page_num)
            page_num += 1
            if len(images) > 0:
                yield np.array(images[0])

    @staticmethod
    def get_concat_v(images: List[Image.Image]) -> Image:
        if len(images) == 1:
            return images[0]
        width = max((image.width for image in images))
        height = sum((image.height for image in images))
        dst = Image.new('RGB', (width, height))
        height = 0
        for image in images:
            dst.paste(image, (0, height))
            height += image.height
        return dst

