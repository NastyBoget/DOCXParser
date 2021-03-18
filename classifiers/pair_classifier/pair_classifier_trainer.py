import gzip
import json
import logging
import os
import pickle
from collections import Counter
from typing import List, Tuple

from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from tqdm import tqdm
from xgboost import XGBClassifier

from classifiers.abstract_classifier_trainer import AbstractClassifierTrainer


class PairClassifierTrainer(AbstractClassifierTrainer):

    def _get_data(self) -> List[dict]:
        with open(self.data_path) as data_file:
            labeled_data = json.load(data_file)
        return list(labeled_data.values())

    def _cross_val(self, data: List[dict]):
        error_cnt = Counter()
        errors_path = os.path.join(self.path_log, "errors")
        os.makedirs(errors_path, exist_ok=True)
        os.system("rm -rf {}/*".format(errors_path))
        accuracy_scores = []
        f1_scores = []
        min_f1 = 1.

        for iteration in tqdm(range(10)):
            labeled_data_train, labeled_data_val = train_test_split(data, train_size=self.train_size,
                                                                    random_state=iteration)
            data_train, labels_train = self._get_from_labeled_data(labeled_data_train)
            data_val, labels_val = self._get_from_labeled_data(labeled_data_val)
            features_train = self.feature_extractor.fit_transform(data_train)
            features_val = self.feature_extractor.transform(data_val)
            assert features_train.shape[1] == features_val.shape[1]
            cls = XGBClassifier(random_state=iteration, **self.classifier_parameters)
            cls.fit(features_train, labels_train)
            labels_predict = cls.predict(features_val)

            for y_pred, y_true, line in zip(labels_predict, labels_val, data_val):
                if y_true != y_pred:
                    error_cnt[(y_true, y_pred)] += 1
                    with open(os.path.join(errors_path, "{}_{}.txt".format(y_true, y_pred)), "a") as file:
                        line_with_label = {"label": y_true, "uid": f"{line[0]['uid']}_{line[1]['uid']}", "data": line}
                        file.write(json.dumps(line_with_label, ensure_ascii=False) + "\n")
            accuracy_scores.append(accuracy_score(labels_val, labels_predict))
            f1 = f1_score(labels_val, labels_predict, average="macro")
            if min_f1 > f1:
                min_f1 = f1
                self.y_val = labels_val
                self.y_pred = labels_predict
            f1_scores.append(f1)

        accuracy_scores_dict = self._create_scores_dict(accuracy_scores)
        f1_scores_dict = self._create_scores_dict(f1_scores)
        self._save_errors(error_cnt, errors_path)
        self._plot_confusion_matrix(labels=['equals', 'greater', 'less'])
        return accuracy_scores_dict, f1_scores_dict

    def fit(self, cross_val_only: bool = False):
        data = self._get_data()
        accuracy_scores, f1_scores = self._cross_val(data)
        logging.info(json.dumps(accuracy_scores, indent=4))
        print(f"Accuracy: {accuracy_scores}")
        print(f"F1-measure: {f1_scores}")
        if not cross_val_only:
            data_train, labels_train = self._get_from_labeled_data(data)
            features_train = self.feature_extractor.fit_transform(data_train)
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
                    print("Accuracy: ", file=file)
                    json.dump(obj=accuracy_scores, fp=file, indent=4)
                    print(file=file)
                    print("F1-measure: ", file=file)
                    json.dump(obj=f1_scores, fp=file, indent=4)

    def _get_from_labeled_data(self, labeled_data: List[dict]) -> Tuple[List[List[dict]], List[str]]:
        data = []
        labels = []
        for item in labeled_data:
            data.append(item['data'])
            labels.append(item["label"])
        return data, labels
