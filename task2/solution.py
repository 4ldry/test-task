import datasets
from tree_sitter import Parser, Language, Node
import tree_sitter_python as tspython
from pathlib import Path
from dataclasses import dataclass
from typing import Any


@dataclass
class Solution:
    py_language: Language = Language(tspython.language())
    parser: Parser = Parser(language=py_language)

    def load_dataset(self) -> datasets.Dataset:
        return datasets.load_dataset(path="code-search-net/code_search_net", name="python", split="test", trust_remote_code=True, cache_dir=Path(__file__).parent / "datasets")
    
    def get_root_node_from_source_code(self, source_code: str) -> Node:
        tree = self.parser.parse(source_code.encode())
        root_node = tree.root_node
        return root_node
        
    def process_root_node(self, root_node: Node) -> dict:
        pattern_docs = """
        (
            (function_definition
                body: (
                    block (
                        expression_statement (string) @docstring
                    )
                )
            )
        )
        """
        pattern_coms = """
        (
            (comment) @comment
        )
        """
        pattern_func = """
        (
            (function_definition) @function
        )
        """
        pattern_func_name = """
        (
            function_definition
                name: identifier @func_name
        )
        """
        query_docs = self.py_language.query(pattern_docs)
        query_coms =  self.py_language.query(pattern_coms)
        query_func_name = self.py_language.query(pattern_func_name)
        query_func = self.py_language.query(pattern_func)
        capture_docs = query_docs.captures(root_node)
        capture_coms = query_coms.captures(root_node)
        capture_func_name = query_func_name.captures(root_node)
        capture_func = query_func.captures(root_node)
        func_node = capture_func[0][0]
        func_code = source_code[func_node.start_byte:func_node.end_byte]
        func_name_node = capture_func_name[0][0]
        coms_pos = []
        for coms_node, _ in capture_coms:
            if func_node.start_byte <= coms_node.start_byte < func_node.end_byte:
                coms_pos.append((coms_node.start_byte - func_node.start_byte,
                                    coms_node.end_byte - func_node.end_byte))
        docs_pos = []
        for docs_node, _ in capture_docs:
            if func_node.start_byte <= docs_node.start_byte < docs_node.end_byte:
                docs_pos.append((docs_node.start_byte - func_node.start_byte,
                                    docs_node.end_byte - docs_node.end_byte))
        func_name = func_code[func_name_node.start_byte:func_name_node.end_byte]
        func_body = func_code[func_name_node.end_byte:]
        func_body_wo_coms_and_docs = ""
        last_pos = 0
        for start_pos, end_pos in sorted(coms_pos):
            func_body_wo_coms_and_docs += func_code[last_pos:start_pos]
            last_pos = end_pos
        func_body_wo_coms_and_docs += func_code[last_pos:]
        func_body_masked_name = func_code[:func_name_node.start_byte] + "<NAME_MASK>" + func_code[func_name_node.end_byte+1:]
        return dict()

    def save_result_to_new_dataset(self) -> None:
        pass

def main():
    solution = Solution()
    with open("result.jsonl", "wt") as output:
        for record in Solution.load_dataset():
            source_code = record["original_string"]
            root_node = solution.get_root_node_from_source_code(source_code)
            result = solution.process_root_node(root_node)
            solution.save_result_to_new_dataset(result)

if __name__ == "__main__":
    main()