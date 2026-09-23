import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from backend.config import GEMINI_API_KEY, OPENAI_API_KEY

class LLMService:
    def __init__(self):
        self.gemini_available = bool(GEMINI_API_KEY.strip()) if GEMINI_API_KEY else False

    def generate_candidate_explanation(
        self,
        candidate_name: str,
        match_score: float,
        matching_skills: List[str],
        missing_skills: List[str],
        jd_title: str
    ) -> str:
        """
        Generates explainable rationale for candidate match score.
        Uses Gemini REST API if available, otherwise uses deterministic rule-based template.
        """
        score_pct = int(round(match_score * 100))

        if self.gemini_available:
            try:
                prompt = f"""
                You are an AI Talent Acquisition Assistant for campus placements.
                Generate a concise, professional 2-sentence explanation for a candidate evaluation.
                
                Candidate Name: {candidate_name}
                Target Role: {jd_title}
                Match Score: {score_pct}%
                Matching Skills: {', '.join(matching_skills) if matching_skills else 'None'}
                Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}
                
                Explain why the candidate received this score based on their matching and missing skills.
                Keep it direct and objective.
                """
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY.strip()}"
                payload = json.dumps({
                    "contents": [{"parts": [{"text": prompt}]}]
                }).encode("utf-8")
                
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text:
                        return text
            except Exception as e:
                print(f"LLM API REST call failed or rate-limited: {e}. Falling back to rule-based explanation.")

        # Fallback Explainability Template Engine
        return self._generate_fallback_explanation(candidate_name, score_pct, matching_skills, missing_skills, jd_title)

    def _generate_fallback_explanation(
        self,
        candidate_name: str,
        score_pct: int,
        matching_skills: List[str],
        missing_skills: List[str],
        jd_title: str
    ) -> str:
        """Rule-based explainability generation when LLM API is unavailable/unconfigured."""
        match_str = ", ".join(matching_skills[:4]) if matching_skills else "general profile"
        miss_str = ", ".join(missing_skills[:3]) if missing_skills else "none"

        if score_pct >= 80:
            return (f"Exceptional match ({score_pct}%) for the {jd_title} role. Candidate demonstrates strong alignment "
                    f"in core skills including {match_str}. Minor or no skill gaps identified ({miss_str}).")
        elif score_pct >= 60:
            return (f"Good potential candidate ({score_pct}%) for {jd_title}. Demonstrates core proficiency in {match_str}, "
                    f"though additional training or experience may be required in {miss_str}.")
        elif score_pct >= 40:
            return (f"Moderate match ({score_pct}%) for {jd_title}. Possesses foundational skills like {match_str}, "
                    f"but lacks key required competencies in {miss_str}.")
        else:
            return (f"Low match score ({score_pct}%) for {jd_title}. Candidate lacks essential technical requirements "
                    f"such as {miss_str}, showing limited overlap with the specified job criteria.")

# Singleton instance
llm_service = LLMService()

