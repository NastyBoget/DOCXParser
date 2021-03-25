import os
from typing import Optional

from ete3 import Tree
from ete3.coretype.tree import TreeError

from classifiers.utils import doc2tree

data_path = "/Users/anastasiabogatenkova/DOCXParser/data/test_labeled_pair.json"
test_path = "/Users/anastasiabogatenkova/DOCXParser/data/test"


def convert_to_ete_tree(doc_tree: dict,
                        parent: Optional[Tree] = None) -> Optional[Tree]:
    if parent is None:
        tree = Tree()
        parent = tree.add_child(name="root")
    else:
        tree = None

    for i, subtree in enumerate(doc_tree["children"]):
        node_name = f"{subtree['data']['uid']}_{subtree['data']['text'][:5]}"
        current_node = parent.add_child(name=node_name)
        convert_to_ete_tree(subtree, current_node)

    return tree


def compare_trees(t1: dict, t2: dict) -> float:
    tree_1 = convert_to_ete_tree(t1)
    tree_2 = convert_to_ete_tree(t2)
    rf_dict = tree_1.compare(tree_2)
    rf, rf_max = rf_dict["rf"], rf_dict["max_rf"]
    return rf / rf_max


if __name__ == "__main__":
    results = {}
    for doc_name in os.listdir(test_path):
        if not doc_name.endswith(".docx"):
            continue
        abs_doc_name = os.path.join(test_path, doc_name)
        doc_tree_1 = doc2tree(abs_doc_name)
        doc_tree_2 = doc2tree(abs_doc_name, comparator_type="test", data_path=data_path)
        try:
            compare_result = compare_trees(doc_tree_1, doc_tree_2)
        except TreeError as e:
            print(e)
            print(doc_name)
            continue
        print(f"{doc_name}: {compare_result}")
        results[doc_name] = compare_result
        os.makedirs("resources", exist_ok=True)
    mean_rf = sum(results.values()) / len(results.values())
    results["mean_rf"] = mean_rf
    print(f"mean rf = {mean_rf}")
    with open('resources/results.txt', "w") as f:
        print(results, file=f)
