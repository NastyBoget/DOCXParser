import os
from abc import ABC, abstractmethod
from collections import Counter, OrderedDict
from statistics import mean
from typing import Optional, Callable

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix

from classifiers.abstract_features_extractor import AbstractFeatureExtractor
from classifiers.utils import identity
from classifiers.utils import plot_confusion_matrix


class AbstractClassifierTrainer(ABC):

    def __init__(self,
                 data_path: str,
                 feature_extractor: AbstractFeatureExtractor,
                 path_out: str,
                 path_log: Optional[str] = None,
                 train_size: float = 0.75,
                 classifier_parameters: dict = None,
                 label_transformer: Callable[[str], str] = None,
                 random_seed=42):

        self.data_path = data_path
        self.feature_extractor = feature_extractor
        self.random_seed = random_seed
        assert train_size > 0
        assert train_size < 1 or 1 < train_size < 100
        self.train_size = train_size if train_size < 1 else train_size / 100
        self.classifier_parameters = {} if classifier_parameters is None else classifier_parameters
        self.path_log = path_log

        self.label_transformer = identity if label_transformer is None else label_transformer

        if path_out.endswith(".pkl"):
            path_out += ".gz"
        elif path_out.endswith("pkl.gz"):
            pass
        else:
            path_out += ".pkl.gz"
        self.path_out = path_out
        self.y_val, self.y_pred = None, None

    def _create_scores_dict(self, scores: list) -> dict:
        scores_dict = OrderedDict()
        scores_dict["mean"] = mean(scores)
        scores_dict["scores"] = scores
        return scores_dict

    def _save_errors(self, error_cnt, errors_path=None):
        if errors_path:
            print("save errors in {}".format(errors_path))
        errors_total_num = sum(error_cnt.values())
        print("{:16s} -> {:16s}\t cnt\t percent".format("true", "predicted"))
        for error, cnt in error_cnt.most_common():
            y_true, y_pred = error
            print("{:16s} -> {:16s} {:06,} ({:02.2f}%)".format(y_true, y_pred, cnt, 100 * cnt / errors_total_num))
        if errors_path is None:
            return
        for file_name in os.listdir(errors_path):
            path_file = os.path.join(errors_path, file_name)
            with open(path_file) as file:
                lines = file.readlines()
            lines_cnt = Counter(lines)
            lines.sort(key=lambda l: (-lines_cnt[l], l))
            path_out = os.path.join(errors_path, "{:04d}_{}".format(
                int(1000 * len(lines) / errors_total_num),
                file_name
            ))
            with open(path_out, "w") as file_out:
                for line in lines:
                    file_out.write(line)
            os.remove(path_file)

    @abstractmethod
    def fit(self, cross_val_only: bool = False):
        pass

    def _plot_confusion_matrix(self, labels):
        cnf_matrix = confusion_matrix(self.y_val, self.y_pred, labels=labels)
        np.set_printoptions(precision=2)

        plt.figure(figsize=(10, 10))
        plot_confusion_matrix(cnf_matrix, classes=labels)
