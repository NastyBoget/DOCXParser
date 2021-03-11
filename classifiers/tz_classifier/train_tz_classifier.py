import os
from typing import Optional

from classifiers.tz_classifier.tz_features_extractor import TzTextFeatures
from classifiers.tz_classifier.tz_classifier_trainer import TzClassifierTrainer


def skip_labels(label: str) -> Optional[str]:
    if label not in ("other", "footer"):
        return label
    return None


resources_path = "/Users/anastasiabogatenkova/DOCXParser/classifiers/tz_classifier/resources"
path_out = os.path.join(resources_path, "tz_classifier.pkl.gz")
data_path = "/Users/anastasiabogatenkova/DOCXParser/data/labeled_tz.json"

feature_extractor = TzTextFeatures()
classifier_parameters = dict(learning_rate=0.2,
                             n_estimators=600,
                             booster="gbtree",
                             max_depth=5,
                             colsample_bynode=0.1,
                             colsample_bytree=1)

trainer = TzClassifierTrainer(
    data_path=data_path,
    feature_extractor=feature_extractor,
    path_out=path_out,
    path_log=resources_path,
    label_transformer=skip_labels,
    classifier_parameters=classifier_parameters,
    random_seed=42,
)

trainer.fit(cross_val_only=False)
