from typing import List

from classifiers.abstract_line_type_classifier import AbstractLineTypeClassifier
from classifiers.pair_classifier.pair_classifier import PairClassifier


class DocumentTreeConstructor:

    def __init__(self, comparator: PairClassifier, line_type_classifier: AbstractLineTypeClassifier = None):
        self.comparator = comparator
        self.line_type_classifier = line_type_classifier

    def construct_tree(self, lines: List[dict], with_type=False) -> dict:
        """
        each node is:
        {"type": some type, "data": {}, "children": [], "parent": {}}
        """
        result_tree = {"type": "root", "children": []}
        if with_type:
            line_types = [line["label"] for line in self.line_type_classifier.predict(lines)]
        else:
            line_types = ["" for _ in lines]

        current_tree = result_tree
        for i, line in enumerate(lines):
            # add the first line
            if current_tree["type"] == "root":
                current_tree = self.__add_node(result_tree, line, line_types, i)
            else:
                compare_result = self.comparator.compare([current_tree["data"], line])
                # go up in the tree hierarchy
                while compare_result == "less":
                    current_tree = current_tree["parent"]
                    if current_tree["type"] == "root":
                        break
                    compare_result = self.comparator.compare([current_tree["data"], line])
                # add new child for current tree
                if current_tree["type"] == "root" or compare_result == "greater":
                    current_tree = self.__add_node(current_tree, line, line_types, i)
                # add
                elif compare_result == "equals":
                    current_tree = self.__add_node(current_tree["parent"], line, line_types, i)
                else:
                    raise Exception("error in tree constructing")
        return result_tree

    def __add_node(self, tree_for_adding: dict, line: dict, line_types: List[str], type_ind: int) -> dict:
        line_type = line_types[type_ind]
        new_node = {"type": line_type, "data": line, "children": [], "parent": tree_for_adding}
        tree_for_adding["children"].append(new_node)
        return new_node
