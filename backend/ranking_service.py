from typing import List, Dict, Any
from backend.config import WEIGHT_SEMANTIC, WEIGHT_SKILLS, WEIGHT_QUALIFICATIONS
from backend.embedding_service import embedding_service
from backend.explainability import analyze_skill_gap, evaluate_qualifications, build_explainable_result

class RankingService:
    def rank_candidates(self, jd_data: Dict[str, Any], candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ranks multiple parsed candidate resumes against a Job Description.
        Calculates composite weighted scores and returns sorted candidates with rank numbers and explainability.
        """
        if not candidates:
            return []

        jd_text = jd_data.get("raw_text", "")
        req_skills = jd_data.get("required_skills", [])
        req_edu = jd_data.get("required_education", [])
        
        # 1. Compute Semantic Similarity via Embeddings & Cosine Similarity
        resume_texts = [cand.get("raw_text", "") for cand in candidates]
        raw_semantic_scores = embedding_service.compute_batch_similarity(jd_text, resume_texts)
        
        ranked_results = []
        
        for idx, cand in enumerate(candidates):
            raw_sem = raw_semantic_scores[idx]
            # TF-IDF cosine similarity for text documents typically ranges between 0.15 and 0.50.
            # Scale non-linearly to 0.0-1.0 range for intuitive percentage visualization.
            semantic_score = min(1.0, float(raw_sem * 1.8))

            
            # 2. Skill match calculation (ratio of required skills matched)
            skill_gap = analyze_skill_gap(cand.get("skills", []), req_skills)
            matching_skills_count = len(skill_gap["matching_skills"])
            total_req_skills = len(req_skills) if req_skills else 1
            skill_score = min(1.0, matching_skills_count / float(total_req_skills)) if req_skills else 0.8
            
            # 3. Qualification score
            qualification_score = evaluate_qualifications(cand.get("education", []), req_edu)
            
            # 4. Composite weighted final match score
            final_score = (
                (WEIGHT_SEMANTIC * semantic_score) +
                (WEIGHT_SKILLS * skill_score) +
                (WEIGHT_QUALIFICATIONS * qualification_score)
            )
            
            # Build detailed explainable result
            result_card = build_explainable_result(
                candidate_data=cand,
                jd_data=jd_data,
                semantic_score=semantic_score,
                skill_score=skill_score,
                qualification_score=qualification_score,
                final_score=final_score
            )
            
            result_card["composite_score"] = float(round(final_score, 4))
            ranked_results.append(result_card)

        # Sort candidates descending by match percentage / composite score, with tie-breakers
        ranked_results.sort(
            key=lambda x: (
                x["composite_score"],
                len(x.get("matching_skills", [])),
                x.get("scores_breakdown", {}).get("semantic_similarity", 0)
            ),
            reverse=True
        )
        
        # Assign rank numbers (1-indexed)
        for rank, cand in enumerate(ranked_results, start=1):
            cand["rank"] = rank

        return ranked_results

ranking_service = RankingService()
