import os
from copy import deepcopy
from typing import Iterable
import numpy as np

from PIL import Image, ImageColor

from images_creators.abstract_docx_images_creator import AbstractDocxImagesCreator, PairedPdf


class PairDocxImagesCreator(AbstractDocxImagesCreator):

    def _create_images_from_pdf(self, pdfs: PairedPdf, tmp_dir: str) -> Iterable[Image.Image]:
        """
        we take two paired pdfs with bboxes and create images from them. Then we return images according to
        page order
        @param pdfs: tuple with path to 2 pdfs and info about used colors
        @param tmp_dir: path where we save intermediate images
        @return:
        """
        many_color_images = self._split_pdf2image(pdfs.many_color_pdf)
        two_color_images = self._split_pdf2image(pdfs.two_color_pdf)
        n = 0
        for two_color, many_color in zip(two_color_images, many_color_images):

            diff = many_color - two_color
            all_masks = np.abs(diff) > 0
            many_color[all_masks] = 255
            height, width, chanels = diff.shape

            original_image = deepcopy(many_color)
            original_image[all_masks.max(axis=2)] = (255, 255, 255)
            colors = np.unique(diff.reshape(height * width, chanels), axis=0)

            colors_dict = {}
            colors_dict_invert = {}
            lines = self.docx_reader.get_lines_with_meta()
            page2color = {line["uid"]: line.get("color", "#ff0000") for line in lines}
            for uid in pdfs.two_colors:
                color = ImageColor.getcolor(
                    "#{}".format(self._color_from_decimal(pdfs.many_colors[uid] - pdfs.two_colors[uid])), "RGB")
                colors_dict[uid] = color
                colors_dict_invert[color] = uid
            assert len(colors_dict) == len(colors_dict_invert)

            colors_len = len(colors)
            for ind_1 in range(colors_len - 1):
                for ind_2 in range(ind_1 + 1, colors_len):
                    error_occured = False
                    image_copy = deepcopy(original_image)
                    ind = [ind_1, ind_2]
                    for color_num in range(len(ind)):
                        color = tuple(colors[ind[color_num]])
                        if not color in colors_dict_invert:
                            error_occured = True
                            break
                        uid = colors_dict_invert.get(color)
                        mask = (diff == color).min(axis=2)
                        bbox_color = page2color.get(uid)
                        if bbox_color is not None:
                            image_copy[mask] = ImageColor.getcolor(bbox_color, "RGB")
                            n += 1
                        else:
                            error_occured = True
                    if not error_occured:
                        yield Image.fromarray(image_copy)
                    else:
                        yield None


if __name__ == "__main__":
    img_creator = PairDocxImagesCreator("../examples/docx2images")
    os.makedirs('../examples/docx2images/jpg_pair', exist_ok=True)
    for i, img in enumerate(img_creator.create_images("doc.docx")):
        if img:
            img.save(f'../examples/docx2images/jpg_pair/{i}.jpg', 'JPEG')
        else:
            print(i)
