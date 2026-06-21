"""Dedicated unit tests for reciprocal rank fusion."""

from retrieval.fusion import ReciprocalRankFusion


class TestReciprocalRankFusion:
    def test_fusion_combines_rankings(self):
        fusion = ReciprocalRankFusion(k=60)
        bm25 = [("CAND_A", 0.9), ("CAND_B", 0.7), ("CAND_C", 0.5)]
        dense = [("CAND_B", 0.95), ("CAND_A", 0.8), ("CAND_D", 0.6)]
        fused = fusion.fuse_rankings(bm25, dense)
        assert len(fused) >= 3
        ids = [item[0] for item in fused]
        assert "CAND_A" in ids
        assert "CAND_B" in ids
        scores = [item[1] for item in fused]
        assert scores == sorted(scores, reverse=True)
