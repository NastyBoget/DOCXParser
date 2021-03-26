import gzip
import json
import logging
import os
import pickle
from collections import Counter, defaultdict
from typing import List

from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from tqdm import tqdm
from xgboost import XGBClassifier

from classifiers.abstract_classifier_trainer import AbstractClassifierTrainer
from classifiers.tz_classifier.tz_classifier import TzLineTypeClassifier
from classifiers.utils import flatten


class TzClassifierTrainer(AbstractClassifierTrainer):

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
        post_error_cnt = Counter()
        errors_path = os.path.join(self.path_log, "errors")
        os.makedirs(errors_path, exist_ok=True)
        os.system("rm -rf {}/*".format(errors_path))
        accuracy_scores = []
        f1_scores = []
        postprocess_accuracy_scores = []
        postprocess_f1_scores = []
        min_post_accuracy = 1.

        for iteration in tqdm(range(10)):
            data_train, data_val = train_test_split(data, train_size=self.train_size, random_state=iteration)
            labels_train = self._get_labels(data_train)
            labels_val = self._get_labels(data_val)
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
            accuracy_scores.append(accuracy_score(labels_val, labels_predict))
            f1_scores.append(f1_score(labels_val, labels_predict, average="macro"))

            postprocessing_classifier = TzLineTypeClassifier(classifier=cls, feature_extractor=self.feature_extractor)
            post_labels_val = []
            post_labels_predict = []
            for data_item in data_val:
                post_labels_val.extend(self._get_labels([data_item]))
                post_labels_predict.extend(self._get_labels([postprocessing_classifier.predict(data_item)]))
            postprocess_f1_scores.append(f1_score(post_labels_val, post_labels_predict, average="macro"))
            post_acc_score = accuracy_score(post_labels_val, post_labels_predict)
            postprocess_accuracy_scores.append(post_acc_score)
            if min_post_accuracy > post_acc_score:
                min_post_accuracy = post_acc_score
                self.y_val = post_labels_val
                self.y_pred = post_labels_predict
            for post_y_pred, post_y_true in zip(post_labels_predict, post_labels_val):
                if post_y_true != post_y_pred:
                    post_error_cnt[(post_y_true, post_y_pred)] += 1

        accuracy_scores_dict = self._create_scores_dict(accuracy_scores)
        f1_scores_dict = self._create_scores_dict(f1_scores)
        post_accuracy_scores_dict = self._create_scores_dict(postprocess_accuracy_scores)
        post_f1_scores_dict = self._create_scores_dict(postprocess_f1_scores)

        self._save_errors(error_cnt, errors_path)
        print("After postprocessing:")
        self._save_errors(post_error_cnt)
        self._plot_confusion_matrix(labels=['title', 'toc', 'item', 'part', 'raw_text'])
        return accuracy_scores_dict, f1_scores_dict, post_accuracy_scores_dict, post_f1_scores_dict

    def fit(self, cross_val_only: bool = False):
        data = self.__get_data()
        accuracy_scores, f1_scores, post_accuracy_scores, post_f1_scores = self._cross_val(data)
        logging.info(json.dumps(accuracy_scores, indent=4))
        print(f"Accuracy: {accuracy_scores}")
        print(f"F1-measure: {f1_scores}")
        print(f"Accuracy after postprocessing: {post_accuracy_scores}")
        print(f"F1-measure after postprocessing: {post_f1_scores}")
        if not cross_val_only:
            labels_train = self._get_labels(data)
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
                print("Accuracy: ", file=file)
                json.dump(obj=accuracy_scores, fp=file, indent=4)
                print(file=file)
                print("F1-measure: ", file=file)
                json.dump(obj=f1_scores, fp=file, indent=4)
                print(file=file)
                print("Accuracy after postprocessing: ", file=file)
                json.dump(obj=post_accuracy_scores, fp=file, indent=4)
                print(file=file)
                print("F1-measure after postprocessing: ", file=file)
                json.dump(obj=post_f1_scores, fp=file, indent=4)

    def _get_labels(self, data: List[List[dict]]):
        result = [line["label"] for line in flatten(data)]
        return result
