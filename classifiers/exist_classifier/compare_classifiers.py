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

from classifiers.abstract_classifier_trainer import AbstractClassifierTrainer
from classifiers.exist_classifier.exist_features_extractor import ExistFeaturesExtractor
from classifiers.tz_classifier.tz_classifier_trainer import TzClassifierTrainer
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
        error_cnt = Counter()
        errors_path = os.path.join(self.path_log, "errors")
        os.makedirs(errors_path, exist_ok=True)
        os.system("rm -rf {}/*".format(errors_path))
        accuracy_scores = []
        f1_scores = []
        min_accuracy = 1.

        for iteration in tqdm(range(10)):
            data_train, data_val = train_test_split(data, train_size=self.train_size, random_state=iteration)
            labels_train = self._get_labels(data_train)
            labels_val = self._get_labels(data_val)
            features_train = self.feature_extractor.fit_transform(data_train)
            features_val = self.feature_extractor.transform(data_val)
            assert features_train.shape[1] == features_val.shape[1]

            cls = RandomForestClassifier(random_state=self.random_seed, **self.classifier_parameters)
            cls.fit(features_train, labels_train)
            labels_predict = cls.predict(features_val)
            for y_pred, y_true, line in zip(labels_predict, labels_val, flatten(data_val)):
                if y_true != y_pred:
                    error_cnt[(y_true, y_pred)] += 1
                    with open(os.path.join(errors_path, "{}_{}.txt".format(y_true, y_pred)), "a") as file:
                        file.write(json.dumps(line, ensure_ascii=False) + "\n")
            acc_score = accuracy_score(labels_val, labels_predict)
            accuracy_scores.append(acc_score)
            f1_scores.append(f1_score(labels_val, labels_predict, average="macro"))

            if min_accuracy > acc_score:
                min_accuracy = acc_score
                self.y_val = labels_val
                self.y_pred = labels_predict

        accuracy_scores_dict = self._create_scores_dict(accuracy_scores)
        f1_scores_dict = self._create_scores_dict(f1_scores)
        print("Existing method errors:")
        self._save_errors(error_cnt, errors_path=errors_path)
        self._plot_confusion_matrix(labels=['title', 'item', 'part', 'raw_text'])
        return accuracy_scores_dict, f1_scores_dict

    def fit(self, cross_val_only: bool = False):
        data = self.__get_data()
        accuracy_scores, f1_scores = self._cross_val(data)
        logging.info(json.dumps(accuracy_scores, indent=4))
        print(f"Accuracy for existing method: {accuracy_scores}")
        print(f"F1-measure for existing method: {f1_scores}")
        if not cross_val_only:
            labels_train = self._get_labels(data)
            features_train = self.feature_extractor.fit_transform(data)
            print("data train shape {}".format(features_train.shape))
            cls = RandomForestClassifier(random_state=self.random_seed, **self.classifier_parameters)
            cls.fit(features_train, labels_train)
            if not os.path.isdir(os.path.dirname(self.path_out)):
                os.makedirs(os.path.dirname(self.path_out))
            with gzip.open(self.path_out, "wb") as output_file:
                pickle.dump((cls, self.feature_extractor.parameters()), output_file)

        if self.path_log is not None:
            scores_path = os.path.join(self.path_log, "scores.txt")
            print("Save scores in {}".format(scores_path))
            with open(scores_path, "a") as file:
                print("\nAccuracy for existing method: ", file=file)
                json.dump(obj=accuracy_scores, fp=file, indent=4)
                print(file=file)
                print("F1-measure for existing method: ", file=file)
                json.dump(obj=f1_scores, fp=file, indent=4)

    def _get_labels(self, data: List[List[dict]]):
        result = [line["label"] for line in flatten(data)]
        return result


def skip_labels(label: str) -> Optional[str]:
    if label not in ("other", "footer", "toc"):
        return label
    return None


if __name__ == "__main__":
    resources_path = "/Users/anastasiabogatenkova/DOCXParser/classifiers/exist_classifier/resources"
    path_out = os.path.join(resources_path, "exist_classifier.pkl.gz")
    tz_path_out = os.path.join(resources_path, "tz_classifier.pkl.gz")
    data_path = "/Users/anastasiabogatenkova/DOCXParser/data/labeled_tz.json"

    feature_extractor = TzTextFeatures()
    classifier_parameters = dict(learning_rate=0.2, n_estimators=600, booster="gbtree", max_depth=5,
                                 colsample_bynode=0.1, colsample_bytree=1)
    trainer = TzClassifierTrainer(
        data_path=data_path,
        feature_extractor=feature_extractor,
        path_log=resources_path,
        path_out=tz_path_out,
        label_transformer=skip_labels,
        classifier_parameters=classifier_parameters,
        random_seed=42,
    )
    trainer.fit(cross_val_only=True)

    feature_extractor = ExistFeaturesExtractor()
    classifier_parameters = dict(n_estimators=600, max_depth=5)
    trainer = CompareClassifiers(
        data_path=data_path,
        feature_extractor=feature_extractor,
        path_out=path_out,
        path_log=resources_path,
        label_transformer=skip_labels,
        classifier_parameters=classifier_parameters,
        random_seed=42,
    )
    trainer.fit(cross_val_only=False)
