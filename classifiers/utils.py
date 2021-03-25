import itertools
import os
from typing import List, Iterable, TypeVar, Optional

import matplotlib.pyplot as plt
import numpy as np

from classifiers.pair_classifier.pair_classifier import PairClassifier
from classifiers.tree_constructor.test_comparator import TestComparator
from classifiers.tree_constructor.tree_constructor import DocumentTreeConstructor
from docx_parser.document_parser import DOCXParser

T = TypeVar("T")


def flatten(data: List[List[T]]) -> Iterable[T]:
    for group in data:
        for item in group:
            yield item


def identity(x: T):
    return x


def list_get(ls: List[T], index: int) -> Optional[T]:
    if 0 <= index < len(ls):
        return ls[index]
    return None


def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title=None,
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    print("Confusion matrix:")
    print(cm)

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    if title is not None:
        plt.title(title, fontsize=20)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45, fontsize=20)
    plt.yticks(tick_marks, classes, fontsize=20)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 fontsize=20,
                 color="white" if cm[i, j] > thresh else "black")

    plt.ylabel('Правильная метка', fontsize=20)
    plt.xlabel('Предсказанная метка', fontsize=20)

    os.makedirs("resources", exist_ok=True)
    plt.savefig('resources/confusion_matrix.png',  bbox_inches='tight')


def doc2tree(doc_name: str, comparator_type: str = "pair", data_path: str = None) -> dict:
    doc_name = os.path.abspath(doc_name)
    if comparator_type == "test":
        assert(data_path is not None)
        comparator = TestComparator(data_path)
    else:
        comparator = PairClassifier.load_pickled(config={})

    docx_parser = DOCXParser()
    docx_parser.parse(doc_name)
    lines = docx_parser.get_lines_with_meta()

    tree_constructor = DocumentTreeConstructor(comparator=comparator)
    doc_tree = tree_constructor.construct_tree(lines)
    return doc_tree
