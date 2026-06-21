import json
from typing import Dict, Set


def load_profiles_for_ids(path: str, ids: Set[str]) -> Dict[str, dict]:
    """Scan a JSONL `path` and return a dict of profiles for candidate_ids in `ids`.

    This is a streaming, single-pass reader that keeps memory proportional to |ids|.
    """
    found: Dict[str, dict] = {}
    if not ids:
        return found
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            cid = obj.get("candidate_id")
            if cid in ids:
                found[cid] = obj
                if len(found) == len(ids):
                    break
    return found
