import re
from typing import List, Iterable, Optional

import numpy as np
from scipy.stats._multivariate import method

from classifiers.abstract_features_extractor import AbstractFeatureExtractor
from classifiers.utils import list_get


class TzTextFeatures(AbstractFeatureExtractor):
    dotted_list_regexp = re.compile(r"^\s*(-|—|−|–|®|•|©|⎯|°|\*| -)")
    named_item_regexp = re.compile(r"^(под)?раздел\s*")

    def __init__(self) -> None:
        super().__init__()

        self.list_item_regexp = [
            self.item_extended_regexp,
            re.compile(r"^\s*[IVX]+"),  # roman numerals
            # https://stackoverflow.com/questions/267399/
            # how-do-you-match-only-valid-roman-numerals-with-a-regular-expression
            self.dotted_list_regexp,
            self.named_item_regexp
        ]
        self.end_regexp = [
            re.compile(r":$"),
            re.compile(r"\.;$"),
            re.compile(r"[а-яА-яё]$")
        ]
        self.styles_regexp = [
            re.compile(r"heading \d+"),
            re.compile(r"(title)|(subtitle)"),
            re.compile(r"list item")
        ]

    def parameters(self) -> dict:
        return {}

    def fit(self, documents: List[dict], y=None):
        return self

    def transform(self, documents: List[List[dict]], y=None) -> np.ndarray:
        result_matrix = None
        lines_num = sum((len(document) for document in documents))
        row_id = 0

        toc_features = self._before_special_line(documents, self.__find_toc)
        tz_features = self._before_special_line(documents, self.__find_tz)

        list_item_features = []
        for document in documents:
            list_item_features.extend(self._list_features(document))
            for line_id, line in enumerate(document):
                line_features = list(self._one_line_features(line_id, line, document))
                if result_matrix is None:
                    result_matrix = np.zeros((lines_num, len(line_features)))
                result_matrix[row_id] = line_features
                row_id += 1
        result_matrix = self.prev_line_features(result_matrix, 3, 3)
        list_item_features = np.array(list_item_features)
        return np.vstack((result_matrix.T, toc_features, tz_features, list_item_features.T)).T

    def _list_features(self, lines: List[dict]) -> List[float]:
        previous_ids = [-1]
        texts = [line["text"].strip().strip() for line in lines]
        matches = map(self.number_regexp.match, texts)
        numbers = [(line_id, match.group()) for line_id, match in enumerate(matches) if match]
        if len(numbers) == 0:
            return [0 for _ in lines]
        line_ids, numbers = zip(*numbers)

        result_numbers = []
        for i in range(len(numbers)):
            one_item = []
            this_item = numbers[i]
            for k in previous_ids:
                prev_item = list_get(numbers, i + k)
                one_item.append(1 if self._can_be_prev_element(this_item=this_item, prev_item=prev_item) else -1)
            one_item = max(one_item)
            result_numbers.append(one_item)
        result = [0 for _ in lines]
        for line_id, one_item in zip(line_ids, result_numbers):
            result[line_id] = one_item
        return result

    def _one_line_features(self, line_id: int, line: dict, document: List[dict]) -> Iterable[float]:
        text = line["text"].lower()

        yield from self._start_regexp(line["text"], self.list_item_regexp)
        yield 1 if self.named_item_regexp.match(text) else 0
        yield 1 if line["text"].strip().isupper() else 0
        yield 1 if line["text"].strip().islower() else 0
        yield int("дней" in text) + int("месяцев" in text)
        yield len(self.year_regexp.findall(text))

        number = self.number_regexp.match(text)
        number = number.group() if number else ""
        yield 1 if number.endswith(".") else 0
        yield len(number.split("."))
        yield max([int(n) for n in number.split(".") if n], default=-1)

        yield self._get_size(line)
        yield self._get_bold(line)
        yield self._get_italic(line)
        yield self._get_underlined(line)
        yield self._get_indentation(line)
        yield self._get_type(line)
        style = self._get_style(line).lower()
        yield self._styles_regexp(style)
        yield self._get_hierarchy_level(line)

        yield len(text)
        yield len(text.split())
        yield int(text.strip() == "содержание")
        yield 1 if "техническое" in text and "задание" in text else 0
        yield line_id
        yield line_id / len(document)

    def _end_regexp(self, line: str):
        matches = 0
        for pattern in self.end_regexp:  # list patterns
            match = pattern.findall(line.lower().strip())
            if match is not None and len(match) > 0:
                matches += 1
                yield 1
            else:
                yield 0
        yield matches

    def _styles_regexp(self, style: str):
        pattern_num = 0
        for pattern in self.styles_regexp:
            match = pattern.match(style)
            if match:
                return pattern_num
            pattern_num += 1
        return pattern_num

    def _before_special_line(self, documents: List[List[dict]], find_special_line: method) -> List[float]:
        """

        @param documents: list of document in form of list of lines (we try to extract features from this documents)
        @param find_special_line: function that find some special line, see __find_toc for example
        @return: list of distances from given line to first special line. If line lay before the special line, then
        distance is negative, if line lay after special line then distance is positive, for special line distance is 0
        If there is no special line in the document then distance is 0 for every line
        """
        result = []
        for document in documents:
            special_line_position = find_special_line(document)
            if special_line_position is None:
                result.extend([0. for _ in document])
            else:
                special_line_id = special_line_position
                for line_id, line in enumerate(document):
                    result.append(line_id - special_line_id)
        return result

    def __find_toc(self, document: List[dict]) -> Optional[int]:
        """
        find start of table of content, we assume that start of toc should contain only one word:
         "содержание" or "оглавление"
        @param document: document in form of list of lines
        @return: index of line in list
        if there is no special line we return None
        """
        for line_id, line in enumerate(document):
            if line["text"].strip().lower() in ("содержание", "оглавление"):
                return line_id
        return None

    def __find_tz(self, document: List[dict]) -> Optional[int]:
        for line_id, line in enumerate(document):
            text = "".join(filter(str.isalpha, line["text"])).lower()
            if text == "техническоезадание" or text == "приложение":
                return line_id
        return None

    def __find_item(self, document: List[dict]) -> Optional[int]:
        for line_id, line in enumerate(document):
            text = "".join(filter(str.isalpha, line["text"])).lower()
            if list(self._start_regexp(text, self.list_item_regexp))[-1] > 0:
                return line_id
        return None
