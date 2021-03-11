import re
from abc import ABC, abstractmethod
from typing import List, Pattern, Iterable, Optional

import numpy as np


class AbstractFeatureExtractor(ABC):
    number_regexp = re.compile(r'^\s*\d+\.?(\d+\.)*\d*')  # 1.1.1 1
    item_regexp = re.compile(r'^\s*[а-я][\)|\}]')
    item_extended_regexp = re.compile(r'^\s*[A-ZА-Яa-zа-яё][\)|\}|\.]')
    year_regexp = re.compile(r"(19\d\d|20\d\d)")

    @abstractmethod
    def parameters(self) -> dict:
        pass

    @abstractmethod
    def fit(self, documents: List[List[dict]], y=None):
        pass

    @abstractmethod
    def transform(self, documents: List[List[dict]], y=None) -> np.ndarray:
        pass

    def fit_transform(self, documents: List[List[dict]], y=None) -> np.ndarray:
        self.fit(documents, y)
        return self.transform(documents)

    @staticmethod
    def _prev_line_features(feature_matrix: np.ndarray, n: int) -> np.ndarray:
        if n > feature_matrix.shape[0]:
            return np.zeros(feature_matrix.shape)
        return np.vstack((np.zeros((n, feature_matrix.shape[1])), feature_matrix[:-n, :]))

    @staticmethod
    def _next_line_features(feature_matrix: np.ndarray, n: int) -> np.ndarray:
        if n > feature_matrix.shape[0]:
            return np.zeros(feature_matrix.shape)
        return np.vstack((feature_matrix[n:, :], np.zeros((n, feature_matrix.shape[1]))))

    def prev_line_features(self, matrix: np.ndarray, n_prev: int, n_next: int) -> np.ndarray:
        prev_line_features = [self._prev_line_features(matrix, i) for i in range(1, n_prev + 1)]
        next_line_features = [self._next_line_features(matrix, i) for i in range(1, n_next + 1)]
        matrices = [matrix] + prev_line_features + next_line_features
        result_matrix = np.hstack(tuple(matrices))
        return result_matrix

    def _start_regexp(self, line: str, regexps: List[Pattern]) -> Iterable[float]:
        matches = 0
        text = line.lower().strip()
        for pattern in regexps:  # list patterns
            match = pattern.match(text)
            if match is not None and match.end() > 0:
                matches += 1
                yield match.end() - match.start()
            else:
                yield 0
        yield matches

    def _get_size(self, line: dict) -> float:
        sizes = [annotation[3] for annotation in line["annotations"] if annotation[0] == "size"]  # font size
        return float(sizes[0]) if len(sizes) > 0 else 0.

    def _get_bold(self, line: dict) -> float:
        bold = [annotation for annotation in line["annotations"] if annotation[0] == "bold"]
        return 1. if len(bold) > 0 else 0

    def _get_indentation(self, line: dict) -> float:
        indentation = [annotation[3] for annotation in line["annotations"] if annotation[0] == "indentation"]
        return float(indentation[0]) if len(indentation) > 0 else 0

    @staticmethod
    def _can_be_prev_element(this_item: Optional[str], prev_item: Optional[str]) -> bool:
        """
        check if prev_item can be the previous element of this item in the correct list
        For example "2" can be previous element of "3", "2.1." can be previous element of "2.1.1"
        If prev_item is None then this_item is the first item in the list and should be 1
        @return:
        """
        if this_item is None:
            return False
        this_item_list = [i for i in this_item.split(".") if len(i) > 0]
        if this_item_list == ["1"]:
            return True
        if prev_item is None:
            return False
        prev_item_list = [i for i in prev_item.split(".") if len(i) > 0]
        if len(prev_item_list) > len(this_item_list):
            return False
        if len(prev_item_list) < len(this_item_list) - 1:
            return False
        this_item_prefix = this_item_list[:-1]
        prev_item_prefix = prev_item_list[:-1]
        if len(prev_item_list) == len(this_item_list) - 1:
            return prev_item_list == this_item_prefix and this_item_list[-1] == "1"
        if len(prev_item_list) == len(this_item_list):
            return prev_item_prefix == this_item_prefix and int(this_item_list[-1]) - int(prev_item_list[-1]) == 1
        raise Exception("Unexpected case where this_item = {} prev_item = {}".format(this_item, prev_item))
