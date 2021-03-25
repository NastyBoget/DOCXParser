import json
from typing import List


class TestComparator:

    def __init__(self, data_path: str):
        with open(data_path) as data_file:
            self.labeled_dict = json.load(data_file)
        self.revert_compare = {"greater": "less", "less": "greater", "equals": "equals"}

    def compare(self, pair: List[dict]) -> str:
        uid_1, uid_2 = pair[0]["uid"], pair[1]["uid"]
        pair_uid = f"{uid_1}_{uid_2}"
        if pair_uid in self.labeled_dict:
            return self.labeled_dict[pair_uid]['label']
        revert_pair_uid = f"{uid_2}_{uid_1}"
        if revert_pair_uid in self.labeled_dict:
            return self.labeled_dict[revert_pair_uid]['label']
        raise KeyError("this pair hasn't label")
