import json
import os
import matplotlib.pyplot as mpl
from collections import defaultdict

dataset_path = os.path.dirname(os.path.realpath(__file__)) + r"\dataset\filtered_traces"
apps = os.listdir(dataset_path)
apps_count = len(apps)
traces_by_len: defaultdict[int, int] = defaultdict(int)


def trace_generator():
    for app_path in apps:
        app_directory = dataset_path + rf"\{app_path}"
        traces = os.listdir(app_directory)
        for trace_path in traces:
            gestures_path = app_directory + rf"\{trace_path}" + r"\gestures.json"
            with open(gestures_path, "r") as file:
                gestures_content = json.load(file)
            trace_length = len(gestures_content)
            yield trace_length, trace_path, app_path

def main():
    traces_count = 0
    max_trace_length = -1
    for trace_length, trace_path, app_path in trace_generator():
        traces_count += 1
        traces_by_len[trace_length] += 1
        if trace_length > max_trace_length:
            max_trace_length = trace_length
            max_trace_num = trace_path
            max_trace_app = app_path        

    print(f"Количество приложений - {apps_count}")
    print(f"Количество трейсов - {traces_count}")
    print(
        f"Самый длинный трейс ({max_trace_length}) - {max_trace_num} в приложении {max_trace_app}"
    )
    mpl.bar(list(traces_by_len.keys()), list(traces_by_len.values()), color="g")
    mpl.title("Распределение трейсов по длине")
    mpl.xlabel("Длина трейсов")
    mpl.ylabel("Кол-во трейсов")
    mpl.savefig("task1/solution1")

if __name__ == "__main__":
    main()