import json
import os
import matplotlib.pyplot as mpl

dataset_path = os.path.dirname(os.path.realpath(__file__)) + r"\dataset\filtered_traces"
apps = os.listdir(dataset_path)
apps_count = len(apps)
traces_by_len: dict[int, int] = dict()

traces_count = 0
max_trace_length = -1

for app_path in apps:
    app_directory = dataset_path + fr"\{app_path}"
    traces = os.listdir(app_directory)
    traces_count += len(traces)
    for trace_path in traces:
        gestures_path = app_directory + fr"\{trace_path}" + r"\gestures.json"
        with open(gestures_path, "r") as file:
            gestures_content = json.load(file)
        trace_length = len(gestures_content)
        if trace_length not in traces_by_len:
            traces_by_len[trace_length] = 1
        else:
            traces_by_len[trace_length] += 1
        if trace_length > max_trace_length:
            max_trace_length = trace_length
            max_trace_num = trace_path
            max_trace_app = app_path

mpl.bar(list(traces_by_len.keys()), list(traces_by_len.values()), color="g")
mpl.xlabel("Длина трейсов")
mpl.ylabel("Кол-во трейсов")
mpl.show()

print(f"Количество приложений - {apps_count}")
print(f"Количество трейсов - {traces_count}")
print(f"Самый длинный трейс ({max_trace_length}) - {trace_path} в приложении {max_trace_app}")