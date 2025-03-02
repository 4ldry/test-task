import datasets
from tree_sitter import Parser, Language
import tree_sitter_python as tspython
from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto
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
    result_func_name = auto()
    result_body_with_coms = auto()
    result_body_no_coms = auto()
    result_masked_no_coms = auto()


@dataclass
class Solution:
    py_language: Language = Language(tspython.language())
    parser: Parser = Parser(language=py_language)

    def load_dataset(self) -> datasets.Dataset:
        return datasets.load_dataset(path="code-search-net/code_search_net", name="python", split="test", trust_remote_code=True, cache_dir=(Path(__file__).parent / "datasets"))
        
    def process_src_code(self, src_code: str) -> dict:
        result = dict()
        for answer in Answer:
            match answer:
                case Answer.result_func_name:
                    result[Answer.result_func_name.name] = self.get_func_name(src_code)
                case Answer.result_body_with_coms:
                    result[Answer.result_body_with_coms.name] = self.remove_header(src_code)
                case Answer.result_body_no_coms:
                    body_no_header = self.remove_header(src_code)
                    result[Answer.result_body_no_coms.name] = self.remove_comments(body_no_header)
                case Answer.result_masked_no_coms:
                    masked_name = self.mask_func_name(src_code)
                    result[Answer.result_masked_no_coms.name] = self.remove_comments(masked_name)
        return result

    def remove_header(self, src_code: str) -> str:
        tree = self.parser.parse(src_code.encode())
        root_node = tree.root_node
        query = self.py_language.query(Pattern.func_body.value)
        captures = query.captures(root_node)
        body_node = captures[0][0]
        new_source_code = src_code[body_node.start_byte:body_node.end_byte]
        return new_source_code

    def mask_func_name(self, src_code: str) -> str:
        tree = self.parser.parse(src_code.encode())
        root_node = tree.root_node
        query = self.py_language.query(Pattern.func_name.value)
        captures = query.captures(root_node)
        node_to_edit = captures[0][0]
        new_text = "<NAME_MASK>"
        new_source_code = (
            src_code[:node_to_edit.start_byte] + new_text + src_code[node_to_edit.end_byte:]
        )
        return new_source_code
    
    def get_func_name(self, src_code: str) -> str:
        tree = self.parser.parse(src_code.encode())
        root_node = tree.root_node
        query = self.py_language.query(Pattern.func_name.value)
        captures = query.captures(root_node)
        func_name_node = captures[0][0]
        name = src_code[func_name_node.start_byte:func_name_node.end_byte]
        return name

    def remove_comments(self, source_code: str) -> str:
        tree = self.parser.parse(source_code.encode())
        root_node = tree.root_node
        query = self.py_language.query(Pattern.docs_coms.value)
        captures = query.captures(root_node)
        new_source_code = source_code
        for node, _ in reversed(captures):
            new_source_code = (
                new_source_code[:node.start_byte] + new_source_code[node.end_byte:]
            ).lstrip("\n")
        return new_source_code

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