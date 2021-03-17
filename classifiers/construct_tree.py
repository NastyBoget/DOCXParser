from typing import Optional

from treelib import Tree

from classifiers.pair_classifier.pair_classifier import PairClassifier
from classifiers.tree_constructor import DocumentTreeConstructor
from classifiers.tz_classifier.tz_classifier import TzLineTypeClassifier
from docx_parser.document_parser import DOCXParser


def create_tree(doc_tree: dict, parent: Optional[str] = None, tree: Optional[Tree] = None) -> Optional[Tree]:
    if parent is None:
        tree = Tree()
        tree.create_node("Root", "0")
        parent = "0"
    for i, subtree in enumerate(doc_tree["children"]):
        node_name = parent + str(i)
        tree.create_node(subtree["data"]["text"], node_name, parent=parent)
        create_tree(subtree, node_name, tree)
    return tree


doc_name = "../data/1611572467_467.docx"

pair_classifier = PairClassifier.load_pickled(config={})
tz_classifier = TzLineTypeClassifier.load_pickled(config={})

docx_parser = DOCXParser()
docx_parser.parse(doc_name)
lines = docx_parser.get_lines_with_meta()
lines_with_label = tz_classifier.predict(lines)
lines = [line for line in lines_with_label if line["label"] != "toc"]

tree_constructor = DocumentTreeConstructor(comparator=pair_classifier, line_type_classifier=tz_classifier)
doc_tree = tree_constructor.construct_tree(lines, with_type=True)

tree = create_tree(doc_tree)
tree.show()
