import os
import re
import sys
import tempfile
import time
import zipfile
import numpy as np
from typing import Iterator, Tuple, Optional
from typing import List

from PIL import Image, ImageColor
from bs4 import BeautifulSoup
from pdf2image import convert_from_path
from document_parser import DOCXParser


class DocxImagesCreator:

    def __init__(self,
                 path2docs: str):
        self.path2docs = path2docs
        self.color_step = 16
        self.first_color = 15
        self.base_color = 0
        self.base_color_step = 1
        self.many_colors_file_name = 'many_colors_doc'
        self.two_colors_file_name = 'two_colors_doc'

    def create_images(self,
                      path: str) -> Iterator[Optional[Image.Image]]:

        docx_reader = DOCXParser(os.path.join(self.path2docs, path))
        with zipfile.ZipFile(os.path.join(self.path2docs, path)) as d:
            with tempfile.TemporaryDirectory() as tmp_dir:
                d.extractall(tmp_dir)
                namelist = d.namelist()

                document_bs = docx_reader.get_document_bs
                paragraph_list = docx_reader.get_paragraph_xml_list
                uids = list(range(len(paragraph_list)))

                # create docx file with bboxes of different colors
                used_many_colors = self.__draw_bboxes(uids, paragraph_list, many_colors=True)
                # document_bs was changed implicitly
                text = re.sub("w:pbdr", "w:pBdr", str(document_bs))
                text = re.sub("w:ppr", "w:pPr", text)
                many_colors_pdf = self.__create_pdf_from_docx(tmp_dir, self.many_colors_file_name, namelist, text)

                # clear document_bs from border tags
                border_tags = document_bs.find_all('w:pbdr')
                for tag in border_tags:
                    tag.decompose()

                # create docx file with bboxes of two interleaving colors
                used_two_colors = self.__draw_bboxes(uids, paragraph_list, many_colors=False)
                # document_bs was changed implicitly
                text = re.sub("pbdr", "pBdr", str(document_bs))
                text = re.sub("w:ppr", "w:pPr", text)
                two_colors_pdf = self.__create_pdf_from_docx(tmp_dir, self.two_colors_file_name, namelist, text)

                # create image with bbox
                many_colors_pages, two_colors_pages = self._split_pdf2image(many_colors_pdf
                                                                            ), self._split_pdf2image(two_colors_pdf)

                yield from self.__get_image(many_colors_pages, two_colors_pages, used_many_colors, used_two_colors)

    def __get_image(self,
                    many_colors_pages: Iterator[np.ndarray],
                    two_colors_pages: Iterator[np.ndarray],
                    used_many_colors: List[int],
                    used_two_colors: List[int]):
        diff_img, img = DocxImagesCreator.__change_page(many_colors_pages, two_colors_pages)
        remained_bboxes = diff_img.copy()
        total_img_num = len(used_many_colors)
        for i, (base_color, changed_color) in enumerate(zip(used_two_colors, used_many_colors)):
            colors = ImageColor.getcolor('#' + DocxImagesCreator.__color_from_decimal(
                changed_color - base_color), "RGB")
            one_bbox_mask = self.__get_mask(diff_img, colors)
            if not one_bbox_mask.any():
                bboxes_mask = self.__get_mask(remained_bboxes, (0, 0, 0), equal=False)
                # there are other bboxes on the page
                if bboxes_mask.any():
                    remained_bboxes[bboxes_mask.T] = (0, 0, 0)
                    yield None
                    continue
                try:
                    diff_img, img = DocxImagesCreator.__change_page(many_colors_pages, two_colors_pages)
                    remained_bboxes = diff_img.copy()
                    one_bbox_mask = self.__get_mask(diff_img, colors)
                    if not one_bbox_mask.any():
                        yield None
                        continue
                except StopIteration:
                    yield None
                    continue
            diff_img_copy = diff_img.copy()
            diff_img_copy[one_bbox_mask.T] = (0, 0, 0)
            other_bboxes_mask = self.__get_mask(diff_img_copy, (0, 0, 0), equal=False)
            img_copy = img.copy()
            # delete current bbox from the difference image
            remained_bboxes[one_bbox_mask.T] = (0, 0, 0)
            # delete other bboxes from image
            img_copy[other_bboxes_mask.T] = ImageColor.getcolor('#ffffff', "RGB")
            # make current bbox red
            img_copy[one_bbox_mask.T] = ImageColor.getcolor('#ff0000', "RGB")
            yield Image.fromarray(img_copy)

    @staticmethod
    def __get_mask(img: np.ndarray,
                   colors: Tuple[int, int, int],
                   equal: bool = True) -> np.ndarray:
        red_column, green_column, blue_column = img.T
        red, green, blue = colors
        if equal:
            mask = (red_column == red) & (blue_column == blue) & (green_column == green)
        else:
            mask = (red_column != red) | (blue_column != blue) | (green_column != green)
        return mask

    def __draw_bboxes(self,
                      uids: List[str],
                      paragraph_list: List[BeautifulSoup],
                      many_colors: bool) -> List[int]:
        if many_colors:
            decimal_color = self.first_color
        else:
            decimal_color = self.base_color
        used_colors = []
        # draw bboxes using different colors
        # if many_colors == False we draw bboxes using
        # only two interleaving colors for correct drawing bboxes in docx
        for uid, paragraph in zip(uids, paragraph_list):
            color = self.__color_from_decimal(decimal_color)
            used_colors.append(decimal_color)
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
    def __change_page(changed_pages: Iterator[np.ndarray],
                      base_pages: Iterator[np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        base_page, changed_page = next(base_pages), next(changed_pages)
        diff_img = changed_page - base_page
        return diff_img, base_page

    @staticmethod
    def __color_from_decimal(decimal_color: int) -> str:
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
        pdf_name = DocxImagesCreator.__docx2pdf(tmp_dir, docx_path)
        # TODO delete this
        DocxImagesCreator.__docx2pdf("examples/docx2images", docx_path)
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
        if sys.platform == 'darwin':
            command = '/Applications/LibreOffice.app/Contents/MacOS/soffice'
        else:
            command = 'libreoffice'
        os.system("{} --headless --convert-to pdf {} --outdir {}".format(command, path, out_dir))
        out_file = '{}/{}pdf'.format(out_dir, os.path.split(path)[-1][:-4])
        DocxImagesCreator.__await_for_conversion(out_file)
        return out_file

    @staticmethod
    def __insert_border(bs_tree: BeautifulSoup,
                        color: str) -> None:
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
        step = 1
        left = 1
        images = None
        while images is None or len(images) > 0:
            images = convert_from_path(path, first_page=left, last_page=left + step - 1)
            left += step
            for image in images:
                yield np.array(image)


if __name__ == "__main__":
    img_creator = DocxImagesCreator("examples/docx2images")
    os.makedirs('examples/docx2images/jpg', exist_ok=True)
    # 55 images should be
    for i, img in enumerate(img_creator.create_images("doc2.docx")):
        if img:
            img.save(f'examples/docx2images/jpg/{i}.jpg', 'JPEG')
        else:
            print(i)
