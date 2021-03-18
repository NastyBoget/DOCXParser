from typing import Optional

from treelib import Tree

from classifiers.pair_classifier.pair_classifier import PairClassifier
from classifiers.tree_constructor.tree_constructor import DocumentTreeConstructor
from classifiers.tz_classifier.tz_classifier import TzLineTypeClassifier
from docx_parser.document_parser import DOCXParser


def visualize_tree(doc_tree: dict,
                   with_type: bool = False,
                   parent: Optional[str] = None,
                   tree: Optional[Tree] = None) -> Optional[Tree]:
    if parent is None:
        tree = Tree()
        tree.create_node("Root", "0")
        parent = "0"
    for i, subtree in enumerate(doc_tree["children"]):
        node_name = parent + str(i)
        if with_type and 'label' in subtree['data']:
            tree.create_node(f"{subtree['data']['label']}: {subtree['data']['text']}", node_name, parent=parent)
            visualize_tree(subtree, True, node_name, tree, )
        else:
            tree.create_node(subtree["data"]["text"], node_name, parent=parent)
            visualize_tree(subtree, False, node_name, tree)
    return tree


if __name__ == "__main__":
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

    tree = visualize_tree(doc_tree, with_type=True)
    tree.show()
