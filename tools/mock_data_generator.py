"""Generate realistic mock data for RCT demo and testing."""

import json
import random
from typing import List, Dict, Tuple


def generate_mock_retrieval(num_candidates: int = 500, seed: int = 42) -> List[Dict]:
    """Generate mock retrieval.json with semantic scores."""
    random.seed(seed)
    retrieval = []
    
    for i in range(num_candidates):
        cid = f"CAND_{i:07d}"
        semantic_score = max(0.0, min(1.0, random.gauss(0.65, 0.15)))
        bm25_score = semantic_score * random.uniform(0.8, 1.0)
        embedding_score = semantic_score * random.uniform(0.9, 1.0)
        
        retrieval.append({
            "candidate_id": cid,
            "semantic_score": round(semantic_score, 4),
            "bm25_score": round(bm25_score, 4),
            "embedding_score": round(embedding_score, 4),
        })
    
    return sorted(retrieval, key=lambda x: x["semantic_score"], reverse=True)


def generate_mock_ranking(candidate_ids: List[str], seed: int = 42) -> List[Dict]:
    """Generate mock ranking.json with behavior signals."""
    random.seed(seed + 100)
    ranking = []
    
    for cid in candidate_ids:
        base_signal = random.gauss(75, 15)
        authenticity = max(0, min(100, base_signal + random.gauss(0, 5)))
        trajectory = max(0, min(100, base_signal + random.gauss(0, 5)))
        behavior = max(0, min(100, base_signal + random.gauss(0, 5)))
        production = max(0, min(100, base_signal + random.gauss(2, 5)))
        
        final_score = (authenticity * 0.25 + trajectory * 0.25 + behavior * 0.25 + production * 0.25) / 100
        
        ranking.append({
            "candidate_id": cid,
            "authenticity_score": round(authenticity, 1),
            "trajectory_score": round(trajectory, 1),
            "behavior_score": round(behavior, 1),
            "production_score": round(production, 1),
            "final_score": round(final_score, 4),
        })
    
    return ranking


def generate_mock_candidates(num_candidates: int = 500, seed: int = 42) -> List[Dict]:
    """Generate mock candidates.jsonl with realistic profiles."""
    random.seed(seed + 200)
    
    companies = [
        "Google", "Meta", "Apple", "Microsoft", "Amazon", "Tesla", "OpenAI", "Anthropic",
        "Netflix", "Stripe", "Figma", "Discord", "Notion", "Canva", "TechCorp", "InnovateLabs"
    ]
    
    titles = [
        "Software Engineer", "Senior Engineer", "Staff Engineer", "ML Engineer",
        "Data Scientist", "Product Manager", "DevOps Engineer", "Backend Engineer"
    ]
    
    skills_pool = [
        "Python", "JavaScript", "TypeScript", "Go", "Rust",
        "React", "Vue", "Node.js", "Django", "FastAPI",
        "AWS", "GCP", "Kubernetes", "Docker", "PostgreSQL",
        "Machine Learning", "System Design", "GraphQL"
    ]
    
    candidates = []
    
    for i in range(num_candidates):
        cid = f"CAND_{i:07d}"
        years_exp = random.randint(1, 15)
        
        candidate = {
            "candidate_id": cid,
            "profile": {
                "name": f"Candidate {i}",
                "years_experience": years_exp,
                "current_title": random.choice(titles),
                "current_company": random.choice(companies),
                "location": random.choice(["San Francisco", "New York", "London", "Bangalore"])
            },
            "career_history": [
                {
                    "company": random.choice(companies),
                    "title": random.choice(titles),
                    "duration_months": random.randint(12, 120)
                }
                for _ in range(random.randint(1, 3))
            ],
            "skills": [
                {
                    "name": random.choice(skills_pool),
                    "proficiency": random.choice(["intermediate", "advanced", "expert"])
                }
                for _ in range(random.randint(5, 12))
            ],
            "education": [
                {
                    "institution": random.choice(["IIT Bombay", "Stanford", "MIT", "UC Berkeley", "State University"]),
                    "degree": random.choice(["Bachelor", "Master"]),
                    "tier": random.choice(["tier_1", "tier_2"])
                }
            ],
            "redrob_signals": {
                "engagement_score": round(random.uniform(40, 100), 1),
                "response_rate": round(random.uniform(0.1, 1.0), 2)
            }
        }
        
        candidates.append(candidate)
    
    return candidates


def save_mock_data(num_candidates: int = 500, seed: int = 42) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Generate all mock data and return as tuple."""
    retrieval = generate_mock_retrieval(num_candidates, seed)
    candidate_ids = [r["candidate_id"] for r in retrieval]
    ranking = generate_mock_ranking(candidate_ids, seed)
    candidates = generate_mock_candidates(num_candidates, seed)
    
    return retrieval, ranking, candidates


if __name__ == "__main__":
    retrieval, ranking, candidates = save_mock_data(500, 42)
    print(f"Generated {len(retrieval)} retrieval records")
    print(f"Generated {len(ranking)} ranking records")
    print(f"Generated {len(candidates)} candidate profiles")
