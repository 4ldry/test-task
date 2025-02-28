import datasets
from tree_sitter import Parser, Language, Node
import tree_sitter_python as tspython
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
from enum import Enum
import json

class Pattern(Enum):
    docs_coms = """
    [
        (expression_statement(string))
        (comment)
    ] @comsdocs
    """
    func_body = """
    (function_definition (block) @func)
    """
    func_name = """
    (function_definition name: (identifier)@func_name)
    """
    func_header = """
    (function_definition ["def" name: (identifier) parameters: (parameters) ":"]@header)
    """

class Answer(Enum):
    result_func_name = ...#(Pattern.func_name,)
    result_body_with_coms = ...#(Pattern.func_body,)
    result_body_no_coms = ...#(Pattern.func_body, Pattern.docs_coms)
    result_masked_no_coms = ...#(Pattern.func_header, Pattern.func_name, Pattern.docs_coms)


@dataclass
class Solution:
    py_language: Language = Language(tspython.language())
    parser: Parser = Parser(language=py_language)

    def load_dataset(self) -> datasets.Dataset:
        return datasets.load_dataset(path="code-search-net/code_search_net", name="python", split="test", trust_remote_code=True, cache_dir=(Path(__file__).parent / "datasets"))
    
    def get_root_node_from_source_code(self, source_code: str) -> Node:
        tree = self.parser.parse(source_code.encode())
        root_node = tree.root_node
        return root_node
        
    def process_root_node(self, root_node: Node, source_code: str) -> dict:
        result = dict()
        func_parts_pos = defaultdict(list)
        for func_part in Pattern:
            query = self.py_language.query(func_part.value)
            captures = query.captures(root_node)
            for node, _ in captures:
                func_parts_pos[func_part.name].append((node.start_byte, node.end_byte))
        for answer in Answer:
            nodes_to_remove = []
            match answer.name:
                case Answer.result_func_name.name:
                    nodes_to_concat = func_parts_pos[Pattern.func_name.name]
                case Answer.result_body_with_coms.name:
                    nodes_to_concat = func_parts_pos[Pattern.func_body.name]
                case Answer.result_body_no_coms.name:
                    nodes_to_concat = func_parts_pos[Pattern.func_body.name]
                    nodes_to_remove = func_parts_pos[Pattern.docs_coms.name]
                case Answer.result_masked_no_coms.name:
                    nodes_to_concat = func_parts_pos[Pattern.func_header.name] + func_parts_pos[Pattern.func_body.name]
                    nodes_to_remove = func_parts_pos[Pattern.docs_coms.name]
            concatted_nodes = self.concat_nodes(nodes_to_concat, nodes_to_remove, source_code)
            result[answer.name] = concatted_nodes
        return result

    def concat_nodes(self, pos_pairs: list[tuple[int, int]], skip_pairs: list[tuple[int, int]], source_code: str) -> str:
        concatted_nodes = ""
        for start_pos, end_pos in sorted(pos_pairs):
            if not ((start_pos, end_pos) in skip_pairs):
                concatted_nodes += source_code[start_pos:end_pos].lstrip(" ")
        return concatted_nodes

def main():
    solution = Solution()
    with open("result.jsonl", "wt", encoding="utf-8") as output:
        for record in solution.load_dataset():
            source_code = record["whole_func_string"]
            root_node = solution.get_root_node_from_source_code(source_code)
            result = solution.process_root_node(root_node, source_code)
            record.update(result)
            json.dump(record, output, ensure_ascii=False)
            output.write("\n")

if __name__ == "__main__":
    main()