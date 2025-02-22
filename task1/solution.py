import json
import matplotlib.pyplot as mpl
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from collections.abc import Generator
import argparse


@dataclass
class Solution:    
    task_path: Path = field(default_factory= lambda: Path(__file__).parent)
    dataset_path: Path = field(default_factory= lambda: Path("dataset/filtered_traces"), init=True)
    gestures: Path = field(default_factory = lambda: Path("gestures.json"))
    traces_by_len: dict[int, int] = field(default_factory=dict)
    apps_count: int = 0
    deepest_tree_length: int = 0
    deepest_tree_app: Path = field(default_factory=Path)
    deepest_tree: str = str()
    deepest_tree_trace: str = str()
    
    def trace_generator(self) -> Generator[tuple[int, Path, Path]]:
        for app_path in (self.task_path / self.dataset_path).iterdir():
            self.apps_count += 1
            traces_path_generator = app_path.iterdir()
            for trace_path in traces_path_generator:
                gestures_path = trace_path / self.gestures
                with open(gestures_path, "r") as file:
                    gestures_content = json.load(file)
                trace_length = len(gestures_content)
                yield trace_length, trace_path, app_path

    def get_deepest_tree(self, ui_tree: Path) -> int:
        with open(ui_tree, "r") as tree:
            tree_contents = json.load(tree)
        if tree_contents and "activity" in tree_contents:
            app_name = Path(tree_contents.get("activity_name")).parent
            node = tree_contents.get("activity").get("root")
        else:
            return 0
        max_depth = 0
        stack = [(node, 1)]
        while stack:
            current_node, depth = stack.pop()
            children = current_node.get("children", [])
            if not children:
                if depth > max_depth:
                    max_depth = depth
            for child in children:
                if child: stack.append((child, depth + 1))
        if max_depth > self.deepest_tree_length:
            self.deepest_tree_app = app_name
            self.deepest_tree = ui_tree.name
            self.deepest_tree_trace = ui_tree.parent.parent.name
        return max_depth

    def solve_problem(self) -> None:
        traces_count = 0
        max_trace_length = -1
        for trace_length, trace_path, app_path in self.trace_generator():
            ui_trees_generator = Path(trace_path / "view_hierarchies").iterdir()
            for ui_tree in ui_trees_generator:
                self.deepest_tree_length = max(self.deepest_tree_length, self.get_deepest_tree(ui_tree))
            traces_count += 1
            if trace_length in self.traces_by_len:
                self.traces_by_len[trace_length] += 1
            else:
                self.traces_by_len[trace_length] = 0
            if trace_length > max_trace_length:
                max_trace_length = trace_length
                max_trace_num = trace_path
                max_trace_app = app_path        
        print(f"Количество приложений - {self.apps_count}")
        print(f"Количество трейсов - {traces_count}")
        print(
            f"Самый длинный трейс ({max_trace_length}) - {max_trace_num.name} в приложении {max_trace_app.name}"
        )
        print(f"Самое глубокое дерево - {self.deepest_tree_length} в приложении {self.deepest_tree_app.name}, часть трейса {self.deepest_tree_trace}")

    def draw_plot(self):
        mpl.bar(list(self.traces_by_len.keys()), list(self.traces_by_len.values()), color="g")
        mpl.title("Распределение трейсов по длине")
        mpl.xlabel("Длина трейсов")
        mpl.ylabel("Кол-во трейсов")
        mpl.savefig(f"{self.task_path}/solution1")

def arg_parser():
    parser = argparse.ArgumentParser(
        description = "Solution for task 1"
    )
    parser.add_argument("-dataset_path", required=False, default="dataset/filtered_traces",type=str, help="Path to dataset folder from current dir")
    args = parser.parse_args()
    return args

def main():
    cli_args = arg_parser()
    _dataset_path = Path(__file__).parent / Path(cli_args.dataset_path)
    solution = Solution(dataset_path=_dataset_path)
    solution.solve_problem()
    solution.draw_plot()

if __name__ == "__main__":
    main()