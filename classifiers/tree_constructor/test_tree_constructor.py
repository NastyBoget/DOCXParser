import json
import os
from typing import List

from docx_parser.document_parser import DOCXParser


class TestTreeConstructor:

    def __init__(self):
        self.num2compare = {"1": "greater", "2": "equals", "3": "less"}
        self.result = []

    def construct_tree(self, lines: List[dict]) -> List[dict]:
        result_tree = {"parent": {}, "children": []}
        self.result = []

        current_tree = result_tree
        for i, line in enumerate(lines):
            # add the first line
            if not current_tree["parent"]:
                current_tree = self.__add_node(result_tree, line)
            else:
                compare_result = self.__compare(current_tree["data"], line)
                # go up in the tree hierarchy
                while compare_result == "less":
                    current_tree = current_tree["parent"]
                    if not current_tree["parent"]:
                        break
                    compare_result = self.__compare(current_tree["data"], line)
                if not compare_result:
                    continue
                # add new child for current tree
                if not current_tree["parent"] or compare_result == "greater":
                    current_tree = self.__add_node(current_tree, line)
                # add
                elif compare_result == "equals":
                    current_tree = self.__add_node(current_tree["parent"], line)
                else:
                    raise Exception("error in tree constructing")
        return self.result

    def __add_node(self, tree_for_adding: dict, line: dict) -> dict:
        new_node = {"type": "", "data": line, "children": [], "parent": tree_for_adding}
        tree_for_adding["children"].append(new_node)
        return new_node

    def __compare(self, line_1: dict, line_2: dict) -> str:
        print(line_1, line_2, sep="\n")
        try:
            result = self.num2compare[input()]
        except KeyError:
            return ""
        item = {"label": result, "data": [line_1, line_2]}
        uids = f"{line_1['uid']}_{line_2['uid']}"
        self.result.append({uids: item})
        return result


if __name__ == "__main__":
    doc_name = "../../data/test/test_2.docx"
    doc_name = os.path.abspath(doc_name)

    docx_parser = DOCXParser()
    docx_parser.parse(doc_name)
    lines = docx_parser.get_lines_with_meta()

    test_tree_constructor = TestTreeConstructor()
    result = test_tree_constructor.construct_tree(lines)
    with open("result_2.json", "w") as f:
        json.dump(result, fp=f)
