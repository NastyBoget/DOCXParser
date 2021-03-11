import gzip
import json
import logging
import os
import pickle
from collections import Counter, defaultdict, OrderedDict
from statistics import mean
from typing import Optional, List, Callable

from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from tqdm import tqdm
from xgboost import XGBClassifier

from classifiers.abstract_features_extractor import AbstractFeatureExtractor
from classifiers.utils import flatten, identity


class TzClassifierTrainer:

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

    def __get_data(self) -> List[List[dict]]:
        """
        loads grouped data from self.data_path
        transforms labels using self.label_transformer
        returns list of line's groups
        """
        with open(self.data_path) as data_file:
            data = json.load(data_file)

        if self.label_transformer is None:
            grouped = data
        else:
            grouped = defaultdict(list)
            for group in data.values():
                for line in group:
                    transformed_label = self.label_transformer(line["label"])
                    if transformed_label is not None:
                        line["label"] = transformed_label
                        grouped[line["group"]].append(line)
        result = list(grouped.values())
        logging.info(Counter([line["label"] for line in flatten(result)]))
        return result

    def _cross_val(self, data: List[List[dict]]):
        error_cnt = Counter()
        errors_path = os.path.join(self.path_log, "errors")
        os.makedirs(errors_path, exist_ok=True)
        os.system("rm -rf {}/*".format(errors_path))
        scores = []

        for iteration in tqdm(range(10)):
            data_train, data_val = train_test_split(data, train_size=self.train_size, random_state=iteration)
            labels_train = self.__get_labels(data_train)
            labels_val = self.__get_labels(data_val)
            features_train = self.feature_extractor.fit_transform(data_train)
            features_val = self.feature_extractor.transform(data_val)
            assert features_train.shape[1] == features_val.shape[1]
            cls = XGBClassifier(random_state=iteration, **self.classifier_parameters)
            cls.fit(features_train, labels_train)
            labels_predict = cls.predict(features_val)
            for y_pred, y_true, line in zip(labels_predict, labels_val, flatten(data_val)):
                if y_true != y_pred:
                    error_cnt[(y_true, y_pred)] += 1
                    with open(os.path.join(errors_path, "{}_{}.txt".format(y_true, y_pred)), "a") as file:
                        file.write(json.dumps(line, ensure_ascii=False) + "\n")
            scores.append(accuracy_score(labels_val, labels_predict))
        scores_dict = OrderedDict()
        scores_dict["mean"] = mean(scores)
        scores_dict["scores"] = scores
        self.__save_errors(error_cnt, errors_path)
        return scores_dict

    def __save_errors(self, error_cnt, errors_path):
        print("save errors in {}".format(errors_path))
        errors_total_num = sum(error_cnt.values())
        print("{:16s} -> {:16s}\t cnt\t percent".format("true", "predicted"))
        for error, cnt in error_cnt.most_common():
            y_true, y_pred = error
            print("{:16s} -> {:16s} {:06,} ({:02.2f}%)".format(y_true, y_pred, cnt, 100 * cnt / errors_total_num))
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

    def fit(self, cross_val_only: bool = False):
        data = self.__get_data()
        scores = self._cross_val(data)
        logging.info(json.dumps(scores, indent=4))
        if not cross_val_only:
            labels_train = self.__get_labels(data)
            features_train = self.feature_extractor.fit_transform(data)
            print("data train shape {}".format(features_train.shape))
            cls = XGBClassifier(random_state=self.random_seed, **self.classifier_parameters)
            cls.fit(features_train, labels_train)
            if not os.path.isdir(os.path.dirname(self.path_out)):
                os.makedirs(os.path.dirname(self.path_out))
            with gzip.open(self.path_out, "wb") as output_file:
                pickle.dump((cls, self.feature_extractor.parameters()), output_file)

            if self.path_log is not None:
                scores_path = os.path.join(self.path_log, "scores.txt")
                print("Save scores in {}".format(scores_path))
                with open(scores_path, "w") as file:
                    json.dump(obj=scores, fp=file, indent=4)

    def __get_labels(self, data: List[List[dict]]):
        result = [line["label"] for line in flatten(data)]
        return result
