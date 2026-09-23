from typing import List, Dict, Any
from backend.nlp_llm_service import llm_service

def analyze_skill_gap(candidate_skills: List[str], required_skills: List[str]) -> Dict[str, List[str]]:
    """Compares candidate skills against JD required skills."""
    cand_set = {s.lower() for s in candidate_skills}
    req_set = {s.lower() for s in required_skills}
    
    # Map back to original casing
    cand_map = {s.lower(): s for s in candidate_skills}
    req_map = {s.lower(): s for s in required_skills}
    
    matching = [req_map[s] for s in req_set.intersection(cand_set)]
    missing = [req_map[s] for s in req_set.difference(cand_set)]
    
    # Candidate extra skills not explicitly in JD
    additional = [cand_map[s] for s in cand_set.difference(req_set)]
    
    return {
        "matching_skills": matching,
        "missing_skills": missing,
        "additional_skills": additional
    }

def evaluate_qualifications(candidate_edu: List[str], required_edu: List[str]) -> float:
    """Evaluates qualification match score (0.0 to 1.0)."""
    if not required_edu:
        return 1.0
        
    cand_edu_str = " ".join(candidate_edu).lower()
    for req in required_edu:
        req_clean = req.lower()
        if "b.tech" in req_clean or "b.e." in req_clean or "bachelor" in req_clean:
            if any(term in cand_edu_str for term in ["b.tech", "b.e.", "bachelor", "bca", "b.sc"]):
                return 1.0
        elif "m.tech" in req_clean or "master" in req_clean or "m.s." in req_clean:
            if any(term in cand_edu_str for term in ["m.tech", "m.s.", "master", "mca", "m.sc"]):
                return 1.0
                
    return 0.7  # Default partial qualification credit

def build_explainable_result(
    candidate_data: Dict[str, Any],
    jd_data: Dict[str, Any],
    semantic_score: float,
    skill_score: float,
    qualification_score: float,
    final_score: float
) -> Dict[str, Any]:
    """Assembles structured explainable report for a candidate."""
    cand_skills = candidate_data.get("skills", [])
    req_skills = jd_data.get("required_skills", [])
    
    skill_analysis = analyze_skill_gap(cand_skills, req_skills)
    
    explanation = llm_service.generate_candidate_explanation(
        candidate_name=candidate_data.get("name", "Candidate"),
        match_score=final_score,
        matching_skills=skill_analysis["matching_skills"],
        missing_skills=skill_analysis["missing_skills"],
        jd_title=jd_data.get("title", "Job Position")
    )

    exp_years = candidate_data.get("experience_years", 0)
    exp_score = min(100.0, round(60.0 + (exp_years * 20.0), 1)) if exp_years is not None else 60.0

    projects = candidate_data.get("projects", [])
    proj_score = min(100.0, round(50.0 + (len(projects) * 15.0), 1)) if projects else 50.0

    return {
        "candidate_id": candidate_data.get("candidate_id", ""),
        "candidate_name": candidate_data.get("name", "Unknown Candidate"),
        "filename": candidate_data.get("filename", ""),
        "overall_match_percentage": int(round(final_score * 100)),
        "scores_breakdown": {
            "semantic_similarity": round(semantic_score * 100, 1),
            "skill_coverage": round(skill_score * 100, 1),
            "skill_match": round(skill_score * 100, 1),
            "education": round(qualification_score * 100, 1),
            "qualification_match": round(qualification_score * 100, 1),
            "experience": exp_score,
            "project_relevance": proj_score
        },
        "matching_skills": skill_analysis["matching_skills"],
        "missing_skills": skill_analysis["missing_skills"],
        "additional_skills": skill_analysis["additional_skills"],
        "education": candidate_data.get("education", []),
        "projects": projects,
        "experience_years": exp_years,
        "explanation": explanation
    }
