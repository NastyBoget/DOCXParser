import json
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import pandas as pd

TEST_DIR = "test"


def collect_test_data():
    test_data = {}
    files = os.listdir(TEST_DIR)
    for file in files:
        if not file.endswith(".json"):
            continue
        with open(os.path.join(TEST_DIR, file), "r") as f:
            d = json.load(f)
        for item in d:
            for key, value in item.items():
                test_data[key] = value
    print(len(test_data))
    with open("test_labeled_pair.json", "w") as w_f:
        json.dump(test_data, fp=w_f)


def get_paragraph_classes_amount(file_name):
    with open(file_name) as file:
        labeled = json.load(file)
    classes_amount = defaultdict(int)
    for item in labeled.values():
        for line in item:
            classes_amount[line["label"]] += 1
    return classes_amount


def get_pair_classes_amount(file_name):
    with open(file_name) as file:
        labeled = json.load(file)
    classes_amount = defaultdict(int)
    for item in labeled.values():
        classes_amount[item["label"]] += 1
    return classes_amount


def draw_distribution_hist(classes_amount, title, file_name, data_limit):
    classes_list = [item for item in zip(classes_amount.values(), classes_amount.keys())]
    classes_list = sorted(classes_list)[::-1]

    classes_num = [item[0] for item in classes_list]
    classes_name = [item[1] for item in classes_list]

    classes_series = pd.Series(classes_num)
    # Plot the figure.
    plt.figure(figsize=(10, 5))
    ax = classes_series.plot(kind='bar', ylim=(0, data_limit), color='green')
    ax.set_title('Распределение классов')
    ax.set_xlabel('Название класса')
    ax.set_ylabel(title)
    ax.set_xticklabels(classes_name, rotation=0)

    rects = ax.patches

    for rect, class_amount in zip(rects, classes_num):
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2, height, class_amount,
                ha='center', va='bottom')
    plt.savefig(file_name)


if __name__ == "__main__":
    cl_amount = get_paragraph_classes_amount("labeled_tz.json")
    draw_distribution_hist(cl_amount, "Количество параграфов", "paragraph_distribution.png", 520)

    cl_amount = get_pair_classes_amount("labeled_pair.json")
    draw_distribution_hist(cl_amount, "Количество пар параграфов", "pair_distribution.png", 2550)
