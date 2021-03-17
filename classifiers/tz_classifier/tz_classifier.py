import gzip
import os
import pickle
from typing import List, Iterable

from xgboost import XGBClassifier

from classifiers.abstract_line_type_classifier import AbstractLineTypeClassifier
from classifiers.abstract_features_extractor import AbstractFeatureExtractor
from classifiers.tz_classifier.tz_features_extractor import TzTextFeatures


class TzLineTypeClassifier(AbstractLineTypeClassifier):
    document_type = "tz"

    def __init__(self, classifier: XGBClassifier, feature_extractor: AbstractFeatureExtractor):
        self.classifier = classifier
        self.feature_extractor = feature_extractor

    @staticmethod
    def load_pickled(path: str = None, *, config: dict) -> "TzLineTypeClassifier":
        if path is None:
            path = os.path.join(os.path.dirname(__file__), "resources", "tz_classifier.pkl.gz")
            path = os.path.abspath(path)
        with gzip.open(path) as file:
            classifier, feature_extractor_parameters = pickle.load(file)
        return TzLineTypeClassifier(classifier=classifier,
                                    feature_extractor=TzTextFeatures(**feature_extractor_parameters))

    def predict(self, lines: List[dict]) -> List[dict]:
        """
        adds to each line its type using key "label"
        type may be "title", "toc", "item", "part", "raw_text"
        """

        predictions = self.__get_predictions(lines)
        result = []

        for prediction, line in zip(predictions, lines):
            line["label"] = prediction
            result.append(line)
        return result

    def __get_predictions(self, lines: List[dict]) -> Iterable[str]:
        """
        get predictions from xgb classifier and patch them according to our prior knowledge. For example we know that
        title can not be interrupted with other structures. Empty line can not be item or toc item (but can be part of
        title or raw_text), there are can not be toc items after body has begun
        @param lines:
        @return:
        """
        features = self.feature_extractor.transform([lines])
        labels_probability = self.classifier.predict_proba(features)

        title_id = list(self.classifier.classes_).index("title")
        raw_text_id = list(self.classifier.classes_).index("raw_text")

        empty_line = [line["text"].strip() == "" for line in lines]
        labels_probability[empty_line, :] = 0
        labels_probability[empty_line, raw_text_id] = 1

        labels = [self.classifier.classes_[i] for i in labels_probability.argmax(1)]
        first_non_title = min((i for i, label in enumerate(labels) if label not in ["title", "raw_text"]), default=0)
        # set probability to one for title before the body or toc
        labels_probability[:first_non_title, :] = 0
        labels_probability[:first_non_title, title_id] = 1

        # zeros probability for title after body of document has begun
        labels_probability[first_non_title:, title_id] = 0

        labels = [self.classifier.classes_[i] for i in labels_probability.argmax(1)]
        assert len(labels) == len(lines)
        yield from labels
