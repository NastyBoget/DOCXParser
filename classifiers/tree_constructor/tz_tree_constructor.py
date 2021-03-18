from typing import List

from classifiers.pair_classifier.pair_classifier import PairClassifier
from classifiers.tz_classifier.tz_classifier import TzLineTypeClassifier


class TzDocumentTreeConstructor:

    def __init__(self, comparator: PairClassifier, line_type_classifier: TzLineTypeClassifier):
        self.comparator = comparator
        self.line_type_classifier = line_type_classifier

    def construct_tree(self, lines: List[dict]) -> dict:
        """
        each node is:
        {"type": some type, "data": {}, "children": [], "parent": {}}
        first root's child includes all title paragraphs
        second root's child includes all toc paragraphs (if they exist)
        remaining paragraphs are included into the greatest title paragraph
        """
        result_tree = {"type": "root", "children": []}
        lines = self.line_type_classifier.predict(lines)
        title_lines = [line for line in lines if line["label"] == "title"]
        toc_lines = [line for line in lines if line["label"] == "toc"]
        self.__build_tree(title_lines, ["title" for _ in title_lines], result_tree, "root")
        if result_tree["children"]:
            greatest_title = result_tree["children"][0]
        else:
            greatest_title = result_tree
        self.__build_tree(toc_lines, ["toc" for _ in toc_lines], greatest_title, "title")
        other_lines = [line for line in lines if line["label"] != "toc" and line["label"] != "title"]
        other_lines_types = [line["label"] for line in other_lines]
        self.__build_tree(other_lines, other_lines_types, greatest_title, "title")
        return result_tree

    def __build_tree(self, lines: List[dict],
                     line_types: List[str],
                     result_tree: dict,
                     root_type: str) -> None:
        current_tree = result_tree
        for i, line in enumerate(lines):
            # add the first line
            if current_tree["type"] == root_type:
                current_tree = self.__add_node(result_tree, line, line_types, i)
            else:
                compare_result = self.comparator.compare([current_tree["data"], line])
                # go up in the tree hierarchy
                while compare_result == "less":
                    current_tree = current_tree["parent"]
                    if current_tree["type"] == root_type:
                        break
                    compare_result = self.comparator.compare([current_tree["data"], line])
                # add new child for current tree
                if current_tree["type"] == root_type or compare_result == "greater":
                    current_tree = self.__add_node(current_tree, line, line_types, i)
                # add
                elif compare_result == "equals":
                    current_tree = self.__add_node(current_tree["parent"], line, line_types, i)
                else:
                    raise Exception("error in tree constructing")

    def __add_node(self, tree_for_adding: dict, line: dict, line_types: List[str], type_ind: int) -> dict:
        line_type = line_types[type_ind]
        new_node = {"type": line_type, "data": line, "children": [], "parent": tree_for_adding}
        tree_for_adding["children"].append(new_node)
        return new_node
