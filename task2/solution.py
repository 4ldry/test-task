import datasets
from tree_sitter import Parser, Language, Node
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
    pattern: str = """
    (function_definition name: (identifier) @func_name)
    (function_definition (block) @func_body)
    (function_definition ["def" name: (identifier) parameters: (parameters) ":"] @header)
    [
        (expression_statement(string))
        (comment)
    ] @comsdocs
    """

    def load_dataset(self) -> datasets.Dataset:
        return datasets.load_dataset(path="code-search-net/code_search_net", name="python", split="test", trust_remote_code=True, cache_dir=(Path(__file__).parent / "datasets"))
        
    def process_src_code(self, src_code: str) -> dict:
        result = dict()
        tree = self.parser.parse(src_code.encode())
        root_node = tree.root_node
        query = self.py_language.query(self.pattern)
        captures = query.captures(root_node)
        nodes: dict = {
            "func_name": None,
            "func_body": None,
            "header": None,
            "comments": []
        }
        for node, tag in captures:
            if tag == "func_name":
                nodes["func_name"] = node
            elif tag == "func_body":
                nodes["func_body"] = node
            elif tag == "header":
                nodes["header"] = node
            elif tag == "comsdocs":
                nodes["comments"].append(node)

        src_code_no_comments = self.remove_comments(nodes["comments"], src_code)
        result[Answer.result_masked_no_coms.name] = self.mask_func_name(nodes["func_name"], src_code_no_comments)

        result[Answer.result_func_name.name] = self.extract_text(nodes["func_name"], src_code)

        body_with_comments = self.extract_text(nodes["func_body"], src_code)
        result[Answer.result_body_with_coms.name] = body_with_comments
        
        result[Answer.result_body_no_coms.name] = self.remove_header(nodes["header"], src_code_no_comments)
        
        return result

    def mask_func_name(self, name_node: Node, src_code: str) -> str:
        return (
            src_code[:name_node.start_byte] +
            "<NAME_MASK>" +
            src_code[name_node.end_byte:]
        )
    
    def remove_header(self, header_node: Node, src_code: str) -> str:
        return src_code[header_node.start_byte:]

    def extract_text(self, node: Node, src_code: str) -> str:
        text = src_code[node.start_byte:node.end_byte]
        return text

    def remove_comments(self, coms_nodes: list[Node], src_code: str) -> str:
        positions = sorted([(node.start_byte, node.end_byte) for node in coms_nodes], reverse=True)
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