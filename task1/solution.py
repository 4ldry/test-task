import json
import matplotlib.pyplot as mpl
from collections import defaultdict
from pathlib import Path
from typing import Generator

class Solution:    
    task_path: Path = Path(__file__).parent
    dataset_path: Path = Path("dataset/filtered_traces")
    gestures: Path = Path("gestures.json")
    traces_by_len: defaultdict[int, int] = defaultdict(int)
    apps_path_generator = Path(task_path / dataset_path).iterdir()
    apps_count: int = 0
    deepest_tree_length: int = 0
    deepest_tree_app: Path
    
    @staticmethod
    def trace_generator() -> Generator:
        for app_path in Solution.apps_path_generator:
            Solution.apps_count += 1
            traces_path_generator = app_path.iterdir()
            for trace_path in traces_path_generator:
                gestures_path = trace_path / Solution.gestures
                with open(gestures_path, "r") as file:
                    gestures_content = json.load(file)
                trace_length = len(gestures_content)
                yield trace_length, trace_path, app_path

    @staticmethod
    def get_tree_depth(app_name: Path, node: dict) -> int:
        if not node:
            return 0
        max_depth = 0
        stack = [(node, 1)]
        while stack:
            current_node, depth = stack.pop()
            children = current_node.get("children", [])
            if not children:
                if depth > max_depth:
                    max_depth = depth
                    Solution.deepest_tree_app = app_name
                for child in children:
                    if child: stack.append((child, depth + 1))
        return max_depth

    @staticmethod
    def main():
        traces_count = 0
        max_trace_length = -1
        for trace_length, trace_path, app_path in Solution.trace_generator():
            ui_trees_generator = Path(trace_path / "view_hierarchies").iterdir()
            for ui_tree in ui_trees_generator:
                with open(ui_tree, "r") as tree:
                    tree_contents = json.load(tree)
                    if tree_contents and "activity" in tree_contents:
                        root = tree_contents.get("activity").get("root")
                        Solution.deepest_tree_length = max(Solution.deepest_tree_length, Solution.get_tree_depth(app_path, root))
            traces_count += 1
            Solution.traces_by_len[trace_length] += 1
            if trace_length > max_trace_length:
                max_trace_length = trace_length
                max_trace_num = trace_path
                max_trace_app = app_path        
        print(f"Количество приложений - {Solution.apps_count}")
        print(f"Количество трейсов - {traces_count}")
        print(
            f"Самый длинный трейс ({max_trace_length}) - {max_trace_num.stem} в приложении {max_trace_app}"
        )
        print(f"Самое глубокое дерево - {Solution.deepest_tree_length} в приложении {Solution.deepest_tree_app}")
        mpl.bar(list(Solution.traces_by_len.keys()), list(Solution.traces_by_len.values()), color="g")
        mpl.title("Распределение трейсов по длине")
        mpl.xlabel("Длина трейсов")
        mpl.ylabel("Кол-во трейсов")
        mpl.savefig(f"{Solution.task_path}/solution1")

Solution.main()