from transformers import T5ForConditionalGeneration, AutoTokenizer
from evaluate import load
from dataclasses import dataclass
import json


@dataclass
class Solution:
    checkpoint = "Salesforce/codet5p-220m"
    device = "cuda"

    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    model = T5ForConditionalGeneration.from_pretrained(checkpoint).to(device)

    def get_preds_refs(self, record: dict) -> tuple[str, str]:
        src_code = record["result_masked_no_coms"]
        encoded = self.tokenizer.encode_plus(
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
        Exact match is {round(em_result, 10)} \n\
        Rouge-1 is {round(rouge_result, 10)}")

    def filter_tokens(self, output, end_token="<extra_id_1>") -> str:
        txt = self.tokenizer.decode(
            output[2:], skip_special_tokens=False, clean_up_tokenization_spaces=False
        )
        if end_token in txt:
            _end_token_index = txt.index(end_token)
            return txt[:_end_token_index].lstrip(" ")
        else:
            return txt.lstrip(" ")


def main():
    solution = Solution()
    predictions = []
    references = []
    with open("result.jsonl", "r", encoding="utf-8") as data:
        for line in data:
            record = json.loads(line)
            pred, ref = solution.get_preds_refs(record)
            predictions.append(pred)
            references.append(ref)
    solution.evaluate_model(predictions, references)


if __name__ == "__main__":
    main()
