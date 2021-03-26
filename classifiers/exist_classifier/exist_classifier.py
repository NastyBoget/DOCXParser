import gzip
import os
import pickle
from typing import List

from sklearn.ensemble import RandomForestClassifier

from classifiers.abstract_features_extractor import AbstractFeatureExtractor
from classifiers.abstract_line_type_classifier import AbstractLineTypeClassifier
from classifiers.exist_classifier.exist_features_extractor import ExistFeaturesExtractor


class ExistClassifier(AbstractLineTypeClassifier):

    def __init__(self, classifier: RandomForestClassifier, feature_extractor: AbstractFeatureExtractor):
        self.classifier = classifier
        self.feature_extractor = feature_extractor

    @staticmethod
    def load_pickled(path: str = None, *, config: dict) -> "ExistClassifier":
        if path is None:
            path = os.path.join(os.path.dirname(__file__), "resources", "exist_classifier.pkl.gz")
            path = os.path.abspath(path)
        with gzip.open(path) as file:
            classifier, feature_extractor_parameters = pickle.load(file)
        return ExistClassifier(classifier=classifier,
                               feature_extractor=ExistFeaturesExtractor(**feature_extractor_parameters))

    def predict(self, lines: List[dict]) -> List[dict]:

        features = self.feature_extractor.transform([lines])
        predictions = self.classifier.predict(features)
        result = []

        for prediction, line in zip(predictions, lines):
            line["label"] = prediction
            result.append(line)
        return result
