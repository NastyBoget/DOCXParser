import abc
import gzip
import pickle
from typing import List


class AbstractLineTypeClassifier(abc.ABC):

    @abc.abstractmethod
    def predict(self, lines: List[dict]) -> List[dict]:
        """
        :param lines: image and bboxes with text, it is useful for feature extraction and label predictions
        :return: lines with metadata and predicted labels and hierarchy levels
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def load_pickled(path: str) -> "AbstractLineTypeClassifier":
        pass

    def _save2pickle(self, path_out: str, parameters: object) -> str:
        if path_out.endswith(".pkl"):
            path_out += ".gz"
        elif path_out.endswith(".gz"):
            pass
        else:
            path_out += ".pkl.gz"
        with gzip.open(path_out, "wb") as file_out:
            pickle.dump(obj=parameters, file=file_out)
        return path_out
