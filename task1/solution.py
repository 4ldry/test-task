import json
import matplotlib.pyplot as mpl
from collections import defaultdict
from pathlib import Path

task_path = Path(__file__).parent
dataset_path = Path("dataset/filtered_traces")
gestures = Path("gestures.json")
traces_by_len: defaultdict[int, int] = defaultdict(int)


apps_path_generator = Path(task_path / dataset_path).iterdir()
apps_count = 0

def trace_generator():
    global apps_count
    for app_path in apps_path_generator:
        apps_count += 1
        traces_path_generator = app_path.iterdir()
        for trace_path in traces_path_generator:
            gestures_path = trace_path / gestures
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
        f"Самый длинный трейс ({max_trace_length}) - {max_trace_num.stem} в приложении {max_trace_app.stem}"
    )
    print(traces_by_len)
    mpl.bar(list(traces_by_len.keys()), list(traces_by_len.values()), color="g")
    mpl.title("Распределение трейсов по длине")
    mpl.xlabel("Длина трейсов")
    mpl.ylabel("Кол-во трейсов")
    mpl.savefig(f"{task_path}/solution1")

if __name__ == "__main__":
    main()