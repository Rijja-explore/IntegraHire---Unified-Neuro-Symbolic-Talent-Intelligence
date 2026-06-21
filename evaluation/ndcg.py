from typing import Dict, List
import math


def dcg_at_k(relevances: List[float], k: int) -> float:
    dcg = 0.0
    for i, rel in enumerate(relevances[:k], start=1):
        denom = math.log2(i + 1)
        dcg += rel / denom
    return dcg


def ndcg_at_k(gold: Dict[str, float], predicted_ids: List[str], k: int) -> float:
    # gold: candidate_id -> relevance
    relevances = [float(gold.get(cid, 0.0)) for cid in predicted_ids[:k]]
    dcg = dcg_at_k(relevances, k)
    # ideal DCG
    ideal_vals = sorted([v for v in gold.values()], reverse=True)[:k]
    idcg = dcg_at_k(ideal_vals, k)
    if idcg == 0:
        return 0.0
    return dcg / idcg


def batch_ndcg(gold_list: List[Dict[str, float]], predicted_list: List[List[str]], k: int) -> List[float]:
    return [ndcg_at_k(g, p, k) for g, p in zip(gold_list, predicted_list)]
