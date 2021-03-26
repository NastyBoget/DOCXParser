import re
from typing import List, Iterator, Union, Tuple

import numpy as np

from classifiers.abstract_features_extractor import AbstractFeatureExtractor


class ExistFeaturesExtractor(AbstractFeatureExtractor):

    def __init__(self) -> None:
        super().__init__()

        self.dash_list = re.compile(r"^\s*[-—−–⎯•*]")
        self.bracket_list = re.compile(r'^\s*[A-ZА-Яa-zа-яё\d]\)')
        self.compound_list = re.compile(r'^\s*(\d+\.?(\d+\.)*\d*)')
        self.list_regexps = [
            re.compile(r"^\s*[IVX]+"),
            self.number_regexp,
            self.bracket_list,
            self.dash_list,
        ]
        self.sentence_end = re.compile(r"[A-ZА-Яa-zа-яё]+\.")

    def parameters(self) -> dict:
        return {}

    def fit(self, documents: List[dict], y=None):
        return self

    def transform(self, documents: List[List[dict]], y=None) -> np.ndarray:
        """
        :param documents: list of documents with paragraphs
        :param y: is not used
        :return: features matrix for the given paragraphs
        """
        result_matrix = None
        lines_num = sum((len(document) for document in documents))
        row_id = 0

        for document in documents:
            max_fs, min_fs = self.__get_max_min_fs(document)
            for line in document:
                line_features = list(self._get_paragraph_features(line))
                line_features.append(self.__get_font_size(line, max_fs, min_fs))
                if result_matrix is None:
                    result_matrix = np.zeros((lines_num, len(line_features)))
                result_matrix[row_id] = line_features
                row_id += 1
        return result_matrix

    def _get_paragraph_features(self, paragraph: dict) -> Iterator[Union[int, float]]:
        """
        returns sequence of features for paragraph
        """
        yield self.__get_indentation(paragraph)
        yield self.__has_period(paragraph)
        yield self.__multiple_sentences(paragraph)
        yield self.__get_alignment(paragraph)
        yield self.__is_bold(paragraph)
        yield self.__item_markers(paragraph)
        yield self.__is_underlined(paragraph)

    def __get_font_size(self, paragraph: dict, max_fs: float, min_fs: float) -> float:
        if max_fs == min_fs:
            return 1.
        fs = self._get_size(paragraph)
        return (fs - min_fs) / (max_fs - min_fs)

    def __get_max_min_fs(self, document: List[dict]) -> Tuple[float, float]:
        max_fs, min_fs = 0, 1000
        for paragraph in document:
            fs = self._get_size(paragraph)
            max_fs = fs if fs > max_fs else max_fs
            min_fs = fs if fs < min_fs else min_fs
        return max_fs, min_fs

    def __get_indentation(self, paragraph: dict) -> int:
        return int(self._get_indentation(paragraph) > 0 or paragraph["text"].startswith("\t") or
                   paragraph["text"].startswith("  "))

    def __has_period(self, paragraph: dict) -> int:
        return int(paragraph["text"].endswith('.'))

    def __multiple_sentences(self, paragraph: dict) -> int:
        matches = self.sentence_end.findall(paragraph["text"])
        return int(len(matches) > 1)

    def __get_alignment(self, paragraph: dict) -> int:
        return self._get_alignment(paragraph)

    def __is_bold(self, paragraph: dict) -> float:
        return self._get_bold(paragraph)

    def __item_markers(self, paragraph: dict) -> int:
        for regexp in self.list_regexps:
            if regexp.match(paragraph["text"]):
                return 1
        return 0

    def __is_underlined(self, paragraph: dict) -> float:
        return self._get_underlined(paragraph)
