import re
from typing import List, Iterator, Union, Pattern

import numpy as np
from scipy.stats._multivariate import method

from classifiers.abstract_features_extractor import AbstractFeatureExtractor


class PairFeaturesExtractor(AbstractFeatureExtractor):

    def __init__(self) -> None:
        super().__init__()

        self.list_beginning = re.compile(r":$")
        self.dash_list = re.compile(r"^\s*[-—−–⎯]")
        self.dot_list = re.compile(r"^\s*•")
        self.bracket_list = re.compile(r'^\s*\d+\)')
        self.bracket_letter_list = re.compile(r'^\s*[А-Яa-zа-яё]\)')
        self.list_regexps = [
            re.compile(r"^\s*[IVX]+"),
            self.number_regexp,
            self.bracket_list,
            self.bracket_letter_list,
            re.compile(r'^\s*–'),
            re.compile(r'^\s*—'),
            self.dot_list,
            re.compile(r'^\s*−'),
            re.compile(r'^\s*\*'),
            re.compile(r'^\s*⎯')
        ]
        self.end_regexps = [
            self.list_beginning,
            re.compile(r"[.;,]$"),
            re.compile(r"[а-яА-Яё\w]$")
        ]

    def parameters(self) -> dict:
        return {}

    def fit(self, documents: List[dict], y=None):
        return self

    def transform(self, pairs: List[List[dict]], y=None) -> np.ndarray:
        """
        :param pairs: list of paragraph pairs
        :param y: is not used
        :return: features matrix for the given pairs
        """
        result_matrix = None
        pairs_num = len(pairs)
        for pair_id, pair in enumerate(pairs):
            pair_features = list(self._get_pair_features(pair))
            if result_matrix is None:
                result_matrix = np.zeros((pairs_num, len(pair_features)))
            result_matrix[pair_id] = pair_features

        return result_matrix

    def _get_pair_features(self, pair: List[dict]) -> Iterator[Union[int, float]]:
        """
        returns sequence of features for pair of paragraphs
        """
        # TODO решить что делать со списками неочевидно вложенными в строки
        # признак содержания
        # процент жирности в тексте
        # use metadata from DOCXParser
        yield self.__get_feature_difference_for_pair(pair, self._get_size)
        yield self.__get_feature_difference_for_pair(pair, self._get_indentation)
        yield self.__get_feature_difference_for_pair(pair, self._get_bold)
        yield self.__get_feature_difference_for_pair(pair, self._get_italic)
        yield self.__get_feature_difference_for_pair(pair, self._get_underlined)
        yield self.__get_feature_difference_for_pair(pair, self._get_alignment)  # TODO change this
        yield self.__get_feature_difference_for_pair(pair, self._get_hierarchy_level)
        yield self.__get_feature_difference_for_pair(pair, self._get_type)
        # detect styles
        yield self.__get_feature_difference_for_pair(pair, lambda x: self._styles_regexp(self._get_style(x).lower()))
        yield int(self.toc_regexp.match(self._get_style(pair[0]).lower()) is None)
        # detect uppercase
        yield self.__get_feature_difference_for_pair(pair, lambda x: int(x["text"].isupper()))
        # detect centering alignment
        yield self.__get_feature_difference_for_pair(pair, lambda x: int(self._get_alignment(x) == 0))
        # detect strings which end with :
        yield self.__get_feature_difference_for_pair(pair, lambda x: int(x["text"].endswith(":")))
        yield self.__get_feature_difference_for_pair(pair, lambda x: int(x["text"].startswith("\t")))
        # detect specific types of lists
        yield self.__get_feature_difference_for_pair(pair, lambda x: int(self.number_regexp.match(x["text"]) is None))
        yield self.__get_feature_difference_for_pair(pair, lambda x: int(self.dash_list.match(x["text"]) is None))
        yield self.__get_feature_difference_for_pair(pair, lambda x: int(self.dot_list.match(x["text"]) is None))
        yield self.__get_feature_difference_for_pair(pair, lambda x: int(self.bracket_list.match(x["text"]) is None))
        yield self.__get_feature_difference_for_pair(pair,
                                                     lambda x: int(self.bracket_letter_list.match(x["text"]) is None))

        yield from self.__compare_list_paragraphs(pair)
        yield self.__compare_regexprs_difference(pair, self.list_regexps)
        yield self.__compare_regexprs_difference(pair, self.end_regexps)
        yield self.__detect_list_beginning(pair)

    def __get_feature_difference_for_pair(self,
                                          pair: List[dict],
                                          get_feature: method) -> Union[int, float]:
        """
        applies method to both elements in pair and returns its difference
        """
        return get_feature(pair[0]) - get_feature(pair[1])

    def __compare_list_paragraphs(self, pair: List[dict]) -> Iterator[int]:
        """
        compares two lists with numbering like 1.1.1
        if such numbering wasn't found value of numberings set 0 by default
        """
        values = [0, 0]
        for i, item in enumerate(pair):
            match = self.number_regexp.match(item["text"])
            if match:
                text = match.string
                if text.endswith('.'):
                    text = text[:-1]
                # count number of numbering points e.g. in 1.1.1 there are 3 numbering points
                values[i] = len(text.split('.'))

        if values[0] == 0 and values[1] == 0:
            yield 0
        else:
            yield 1

        yield values[0] - values[1]

    def __compare_regexprs_difference(self, pair: List[dict], patterns: List[Pattern]) -> int:
        """
        suppose patterns are ordered
        check lines matches and calculate difference between patterns' indices
        """
        patterns_len = len(patterns)
        values = [patterns_len, patterns_len]
        for item_num, item in enumerate(pair):
            for i, pattern in enumerate(patterns):
                match = pattern.match(item["text"])
                if match:
                    values[item_num] = i
                    break
        return values[0] - values[1]

    def __detect_list_beginning(self, pair: List[dict]) -> int:
        """
        detects cases like this
            heading for some list:
            - list item
        """
        values = [1, 1]
        for i, item in enumerate(pair):
            match = self.list_beginning.match(item["text"])
            if match:
                values[i] = 0
                continue
            for expr in self.list_regexps:
                match = expr.match(item["text"])
                if match:
                    values[i] = 2
                    break
        return values[0] - values[1]
