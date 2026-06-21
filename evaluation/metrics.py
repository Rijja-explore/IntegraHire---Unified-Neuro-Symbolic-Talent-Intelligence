from typing import List, Dict
from evaluation.ndcg import ndcg_at_k


def evaluate_queries(gold_list: List[Dict[str, float]], predicted_list: List[List[str]], k: int = 10) -> Dict[str, float]:
    scores = [ndcg_at_k(g, p, k) for g, p in zip(gold_list, predicted_list)]
    return {"mean_ndcg": sum(scores) / len(scores) if scores else 0.0}
