import datasets
from tree_sitter import Parser, Language, Node, Tree
import tree_sitter_python as tspython
from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto
from collections.abc import Generator
import json


class Answer(Enum):
    result_func_name = auto()
    result_body_with_coms = auto()
    result_body_no_coms = auto()
    result_masked_no_coms = auto()


@dataclass
class Solution:
    py_language: Language = Language(tspython.language())
    parser: Parser = Parser(language=py_language)

    def load_dataset(self) -> datasets.Dataset:
        return datasets.load_dataset(
            path="code-search-net/code_search_net",
            name="python",
            split="test",
            trust_remote_code=True,
            cache_dir=(Path(__file__).parent / "datasets"),
        )

    def process_src_code(self, src_code: str) -> dict[str, str]:
        tree = self.parser.parse(src_code.encode())

        func_name, func_body, func_header, comments = self.extract_function_info(tree)

        result = dict()

        src_code_no_comments = self.remove_comments(comments, src_code)
        result[Answer.result_masked_no_coms.name] = self.mask_func_name(
            func_name, src_code_no_comments
        )

        result[Answer.result_func_name.name] = self.extract_text(src_code, func_name)

        body_with_comments = func_body
        result[Answer.result_body_with_coms.name] = self.extract_text(
            src_code, body_with_comments
        )

        result[Answer.result_body_no_coms.name] = self.remove_header(
            func_header, src_code_no_comments
        )

        return result

    def extract_text(self, src_code: str, node: Node) -> str:
        return src_code[node.start_byte : node.end_byte]

    def traverse_tree(self, tree: Tree) -> Generator[Node]:
        cursor = tree.walk()
        reached_root = False
        while not reached_root:
            yield cursor.node
            if cursor.goto_first_child():
                continue
            if cursor.goto_next_sibling():
                continue
            backtracking = True
            while backtracking:
                if not cursor.goto_parent():
                    backtracking = False
                    reached_root = True
                if cursor.goto_next_sibling():
                    backtracking = False

    def extract_function_info(self, tree: Tree) -> tuple[Node, Node, Node, list[Node]]:
        func_name, func_body, func_header = None, None, None
        comments = []
        for node in self.traverse_tree(tree):
            if node.type == "function_definition":
                for subnode in node.children:
                    if subnode.type == "identifier":
                        func_name = subnode
                    elif subnode.type == "block":
                        func_body = subnode
                    else:
                        if func_header is None:
                            func_header = subnode
            elif node.type == "comment" or (
                node.type == "string" and node.parent.type == "expression_statement"
            ):
                comments.append(node)
        return func_name, func_body, func_header, comments

    def mask_func_name(self, name_node: Node, src_code: str) -> str:
        return (
            src_code[: name_node.start_byte]
            + "<NAME_MASK>"
            + src_code[name_node.end_byte :]
        )

    def remove_header(self, header_node: Node, src_code: str) -> str:
        return src_code[header_node.start_byte :]

    def remove_comments(self, coms_nodes: list[Node], src_code: str) -> str:
        positions = sorted(
            [(node.start_byte, node.end_byte) for node in coms_nodes], reverse=True
        )
        for start, end in positions:
            src_code = src_code[:start] + src_code[end:]
        return src_code


def main():
    solution = Solution()
    with open("result.jsonl", "wt", encoding="utf-8") as output:
        for record in solution.load_dataset():
            source_code = record["whole_func_string"]
            result = solution.process_src_code(source_code)
            record.update(result)
            json.dump(record, output, ensure_ascii=False)
            output.write("\n")


if __name__ == "__main__":
    main()
