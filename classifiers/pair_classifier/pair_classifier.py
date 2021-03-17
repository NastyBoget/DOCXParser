import gzip
import os
import pickle
from typing import List

from xgboost import XGBClassifier

from classifiers.abstract_features_extractor import AbstractFeatureExtractor
from classifiers.abstract_line_type_classifier import AbstractLineTypeClassifier
from classifiers.pair_classifier.pair_features_extractor import PairFeaturesExtractor


class PairClassifier(AbstractLineTypeClassifier):

    def __init__(self, classifier: XGBClassifier, feature_extractor: AbstractFeatureExtractor):
        self.classifier = classifier
        self.feature_extractor = feature_extractor

    @staticmethod
    def load_pickled(path: str = None, *, config: dict) -> "PairClassifier":
        if path is None:
            path = os.path.join(os.path.dirname(__file__), "resources", "pair_classifier.pkl.gz")
            path = os.path.abspath(path)
        with gzip.open(path) as file:
            classifier, feature_extractor_parameters = pickle.load(file)
        return PairClassifier(classifier=classifier,
                              feature_extractor=PairFeaturesExtractor(**feature_extractor_parameters))

    def predict(self, pair: List[dict]) -> List[dict]:
        """
        adds to pair its type using key "label"
        type may be "equals", "less", "greater"
        :param pair: [line_with_meta_1, line_with_meta_2]
        :return: [{"label": label, "data": pair}]
        """

        features = self.feature_extractor.transform([pair])
        result = [{"data": pair}]
        result[0]["label"] = self.classifier.predict(features)[0]
        return result
