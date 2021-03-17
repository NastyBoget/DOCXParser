import os

from classifiers.pair_classifier.pair_features_extractor import PairFeaturesExtractor
from classifiers.pair_classifier.pair_classifier_trainer import PairClassifierTrainer


resources_path = "/Users/anastasiabogatenkova/DOCXParser/classifiers/pair_classifier/resources"
path_out = os.path.join(resources_path, "pair_classifier.pkl.gz")
data_path = "/Users/anastasiabogatenkova/DOCXParser/data/labeled_pair.json"

feature_extractor = PairFeaturesExtractor()
trainer = PairClassifierTrainer(
    data_path=data_path,
    feature_extractor=feature_extractor,
    path_out=path_out,
    path_log=resources_path,
    random_seed=42,
)

trainer.fit(cross_val_only=False)
