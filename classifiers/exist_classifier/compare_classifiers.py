import gzip
import json
import logging
import os
import pickle
from collections import Counter, defaultdict
from typing import List
from typing import Optional

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from tqdm import tqdm
from xgboost import XGBClassifier

from classifiers.abstract_classifier_trainer import AbstractClassifierTrainer
from classifiers.exist_classifier.exist_features_extractor import ExistFeaturesExtractor
from classifiers.tz_classifier.tz_features_extractor import TzTextFeatures
from classifiers.utils import flatten


class CompareClassifiers(AbstractClassifierTrainer):

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
        tz_error_cnt = Counter()
        exist_error_cnt = Counter()
        errors_path = os.path.join(self.path_log, "errors")
        os.makedirs(errors_path, exist_ok=True)
        os.system("rm -rf {}/*".format(errors_path))
        tz_accuracy_scores = []
        tz_f1_scores = []
        exist_accuracy_scores = []
        exist_f1_scores = []
        min_exist_accuracy = 1.

        for iteration in tqdm(range(10)):
            data_train, data_val = train_test_split(data, train_size=self.train_size, random_state=iteration)
            labels_train = self._get_labels(data_train)
            labels_val = self._get_labels(data_val)
            features_train = self.feature_extractor.fit_transform(data_train)
            features_val = self.feature_extractor.transform(data_val)
            assert features_train.shape[1] == features_val.shape[1]
            cls = XGBClassifier(random_state=iteration, learning_rate=0.2, n_estimators=600,
                                booster="gbtree", max_depth=5, colsample_bynode=0.1, colsample_bytree=1)
            cls.fit(features_train, labels_train)
            labels_predict = cls.predict(features_val)
            for y_pred, y_true in zip(labels_predict, labels_val):
                if y_true != y_pred:
                    tz_error_cnt[(y_true, y_pred)] += 1
            tz_accuracy_scores.append(accuracy_score(labels_val, labels_predict))
            tz_f1_scores.append(f1_score(labels_val, labels_predict, average="macro"))

            exist_feature_extractor = ExistFeaturesExtractor()
            features_train = exist_feature_extractor.fit_transform(data_train)
            features_val = exist_feature_extractor.fit_transform(data_val)
            cls = RandomForestClassifier(random_state=self.random_seed, n_estimators=600, max_depth=5)
            cls.fit(features_train, labels_train)
            labels_predict = cls.predict(features_val)
            for y_pred, y_true in zip(labels_predict, labels_val):
                if y_true != y_pred:
                    exist_error_cnt[(y_true, y_pred)] += 1
            acc_score = accuracy_score(labels_val, labels_predict)
            exist_accuracy_scores.append(acc_score)
            exist_f1_scores.append(f1_score(labels_val, labels_predict, average="macro"))

            if min_exist_accuracy > acc_score:
                min_exist_accuracy = acc_score
                self.y_val = labels_val
                self.y_pred = labels_predict

        tz_accuracy_scores_dict = self._create_scores_dict(tz_accuracy_scores)
        tz_f1_scores_dict = self._create_scores_dict(tz_f1_scores)
        exist_accuracy_scores_dict = self._create_scores_dict(exist_accuracy_scores)
        exist_f1_scores_dict = self._create_scores_dict(exist_f1_scores)

        print("TzClassifier errors:")
        self._save_errors(tz_error_cnt, errors_path)
        print("Existing method errors:")
        self._save_errors(exist_error_cnt)
        self._plot_confusion_matrix(labels=['title', 'toc', 'item', 'part', 'raw_text'])
        return tz_accuracy_scores_dict, tz_f1_scores_dict, exist_accuracy_scores_dict, exist_f1_scores_dict

    def fit(self, cross_val_only: bool = False):
        data = self.__get_data()
        tz_accuracy_scores, tz_f1_scores, exist_accuracy_scores, exist_f1_scores = self._cross_val(data)
        logging.info(json.dumps(tz_accuracy_scores, indent=4))
        print(f"Tz Accuracy: {tz_accuracy_scores}")
        print(f"Tz F1-measure: {tz_f1_scores}")
        print(f"Accuracy for existing method: {exist_accuracy_scores}")
        print(f"F1-measure for existing method: {exist_f1_scores}")
        if not cross_val_only:
            labels_train = self._get_labels(data)
            exist_feature_extractor = ExistFeaturesExtractor()
            features_train = exist_feature_extractor.fit_transform(data)
            print("data train shape {}".format(features_train.shape))
            cls = RandomForestClassifier(random_state=self.random_seed, n_estimators=600, max_depth=5)
            cls.fit(features_train, labels_train)
            if not os.path.isdir(os.path.dirname(self.path_out)):
                os.makedirs(os.path.dirname(self.path_out))
            with gzip.open(self.path_out, "wb") as output_file:
                pickle.dump((cls, self.feature_extractor.parameters()), output_file)

            if self.path_log is not None:
                scores_path = os.path.join(self.path_log, "scores.txt")
                print("Save scores in {}".format(scores_path))
                with open(scores_path, "w") as file:
                    print("Tz Accuracy: ", file=file)
                    json.dump(obj=tz_accuracy_scores, fp=file, indent=4)
                    print(file=file)
                    print("Tz F1-measure: ", file=file)
                    json.dump(obj=tz_f1_scores, fp=file, indent=4)
                    print(file=file)
                    print("Accuracy for existing method: ", file=file)
                    json.dump(obj=exist_accuracy_scores, fp=file, indent=4)
                    print(file=file)
                    print("F1-measure for existing method: ", file=file)
                    json.dump(obj=exist_f1_scores, fp=file, indent=4)

    def _get_labels(self, data: List[List[dict]]):
        result = [line["label"] for line in flatten(data)]
        return result


def skip_labels(label: str) -> Optional[str]:
    if label not in ("other", "footer"):
        return label
    return None


if __name__ == "__main__":
    resources_path = "/Users/anastasiabogatenkova/DOCXParser/classifiers/exist_classifier/resources"
    path_out = os.path.join(resources_path, "exist_classifier.pkl.gz")
    data_path = "/Users/anastasiabogatenkova/DOCXParser/data/labeled_tz.json"

    feature_extractor = TzTextFeatures()
    trainer = CompareClassifiers(
        data_path=data_path,
        feature_extractor=feature_extractor,
        path_out=path_out,
        path_log=resources_path,
        label_transformer=skip_labels,
        classifier_parameters={},
        random_seed=42,
    )
    trainer.fit(cross_val_only=False)
