from transformers import T5ForConditionalGeneration, AutoTokenizer
from evaluate import load
from dataclasses import dataclass
from datasets import load_dataset, Dataset
import argparse


@dataclass
class Solution:
    checkpoint = "Salesforce/codet5p-220m"
    device = "cuda"

    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    model = T5ForConditionalGeneration.from_pretrained(checkpoint).to(device)

    def load_dataset(self, filepath: str, shuffle: bool) -> Dataset:
        dataset = load_dataset("json", data_files=filepath)
        sample_size = 1000
        if shuffle:
            dataset = dataset.shuffle(seed=42)
        sampled_dataset = dataset["train"].select(range(sample_size))
        return sampled_dataset

    def get_preds_refs(self, record: dict, mode: str) -> tuple[str, str]:
        if mode == "with_coms":
            src_code = record["result_masked_with_coms"]
        elif mode == "no_coms":
            src_code = record["result_masked_no_coms"]
        encoded = self.tokenizer(
            src_code,
            add_special_tokens=True,
            return_tensors="pt",
            max_length=510,
            truncation=True,
        )
        input_ids = encoded["input_ids"].to(self.device)
        outputs = self.model.generate(input_ids=input_ids, num_return_sequences=1)
        pred = list(map(self.filter_tokens, outputs))[0]
        ref = record["result_func_name"]
        return pred, ref

    def evaluate_model(self, predictions: list[str], references: list[str]) -> None:
        em_metric = load("exact_match")
        rouge_metirc = load("rouge")
        em_result = em_metric.compute(references=references, predictions=predictions)[
            "exact_match"
        ]
        rouge_result = rouge_metirc.compute(
            references=references, predictions=predictions
        )["rouge1"]
        print(f"\
        Exact match is {round(em_result, 4)} \n\
        Rouge-1 is {round(rouge_result, 4)}")

    def filter_tokens(self, output, end_token="<extra_id_1>") -> str:
        txt = self.tokenizer.decode(
            output[2:], skip_special_tokens=False, clean_up_tokenization_spaces=False
        )
        if end_token in txt:
            _end_token_index = txt.index(end_token)
            return txt[:_end_token_index].lstrip(" ")
        else:
            return txt.lstrip(" ")


def arg_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Solution for task 3")
    parser.add_argument(
        "-dataset_mode",
        required=True,
        choices=["with_coms", "no_coms"],
        type=str,
        help="Choice between funcs' data with coms and w/o coms",
    )
    parser.add_argument(
        "-dataset_filepath",
        required=False,
        default="result.jsonl",
        type=str,
        help="Path to dataset file from current dir",
    )
    args = parser.parse_args()
    return args


def main():
    cli_args = arg_parser()
    mode = cli_args.dataset_mode
    filepath = cli_args.dataset_filepath
    solution = Solution()
    predictions = []
    references = []
    dataset = solution.load_dataset(filepath=filepath, shuffle=False)
    for record in dataset:
        pred, ref = solution.get_preds_refs(record, mode)
        predictions.append(pred)
        references.append(ref)
    solution.evaluate_model(predictions, references)


if __name__ == "__main__":
    main()
