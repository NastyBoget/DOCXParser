import os
from collections import defaultdict
from copy import deepcopy
from typing import Iterable
import numpy as np

from PIL import Image, ImageColor

from images_creators.abstract_docx_images_creator import AbstractDocxImagesCreator, PairedPdf


class DocxImagesCreator(AbstractDocxImagesCreator):

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
        uid2path = defaultdict(list)
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

            for color in colors:
                color = tuple(color)
                if color in colors_dict_invert:
                    uid = colors_dict_invert.get(color)
                    mask = (diff == color).min(axis=2)
                    bbox_color = page2color.get(uid)
                    if bbox_color is not None:
                        image_copy = deepcopy(original_image)
                        image_copy[mask] = ImageColor.getcolor(bbox_color, "RGB")
                        path = "{}/{:06d}.png".format(tmp_dir, n)
                        n += 1
                        uid2path[uid].append(path)
                        Image.fromarray(image_copy).save(path)
        lines = self.docx_reader.get_lines_with_meta()
        for line in lines:
            uid = line["uid"]
            if uid in uid2path:
                images = [Image.open(image_path) for image_path in uid2path[uid]]
                yield self.get_concat_v(images)
            else:
                yield None


if __name__ == "__main__":
    img_creator = DocxImagesCreator("examples/docx2images")
    os.makedirs('examples/docx2images/jpg', exist_ok=True)
    for i, img in enumerate(img_creator.create_images("doc.docx")):
        if img:
            img.save(f'examples/docx2images/jpg/{i}.jpg', 'JPEG')
        else:
            print(i)
