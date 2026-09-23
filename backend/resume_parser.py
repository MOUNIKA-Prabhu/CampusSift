import re
import io
from typing import Dict, Any, List
from pypdf import PdfReader
from backend.config import SKILL_TAXONOMY

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract raw text from PDF file bytes using PyPDF."""
    text = ""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        print(f"Error parsing PDF: {e}")
    return text.strip()

def extract_name(text: str, filename: str = "") -> str:
    """Extract candidate name from first few lines of resume with robust noise filtering."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines[:8]:
        # Filter out PDF headers, binary noise, and common non-name headers
        if re.search(r'(%pdf|pdf-|resume|curriculum|cv|contact|email|phone|profile|http|www|page|table)', line, re.IGNORECASE):
            continue
        # Clean non-alphabetical characters except spaces and dots
        clean_line = re.sub(r'[^a-zA-Z\s\.]', '', line).strip()
        words = clean_line.split()
        if clean_line and 1 <= len(words) <= 4 and len(clean_line) >= 3:
            return clean_line.title()

    # Fallback to filename if text parsing didn't find a clean name
    if filename:
        base_name = re.sub(r'\.pdf$', '', filename, flags=re.IGNORECASE)
        base_name = re.sub(r'\(\d+\)$', '', base_name).strip()  # Strip duplicate copy suffixes like (1), (2)
        base_name = re.sub(r'[^a-zA-Z\s_]', ' ', base_name)
        base_name = re.sub(r'[_\s]+', ' ', base_name).strip()
        if base_name and len(base_name) >= 2:
            return base_name.title()

    return "Unknown Candidate"

def extract_skills(text: str) -> List[str]:
    """Extract skills present in text based on skill taxonomy and pattern matching."""
    extracted = []
    text_lower = text.lower()
    
    for skill in SKILL_TAXONOMY:
        # Match exact word bound for skills like C++, C#, AWS, SQL, NLP
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            extracted.append(skill)
            
    return list(set(extracted))

def extract_education(text: str) -> List[str]:
    """Extract education qualifications."""
    degrees = [
        "B.Tech", "Bachelor of Technology", "B.E.", "Bachelor of Engineering",
        "M.Tech", "Master of Technology", "M.S.", "Master of Science",
        "B.Sc", "Bachelor of Science", "BCA", "MCA", "Ph.D.", "Diploma"
    ]
    found = []
    text_upper = text.upper()
    for degree in degrees:
        if degree.upper() in text_upper:
            found.append(degree)
    return found if found else ["Bachelor's Degree (Inferred)"]

def parse_resume_content(raw_text: str, filename: str = "") -> Dict[str, Any]:
    """Parses raw text from a candidate resume into a structured dictionary."""
    name = extract_name(raw_text, filename=filename)
    skills = extract_skills(raw_text)
    education = extract_education(raw_text)
    
    # Project & Experience Heuristics
    projects = []
    experience_years = 0.0
    
    # Estimate years of experience using keywords or regex like "X years of experience"
    exp_match = re.search(r'(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)\s*(?:of)?\s*experience', raw_text, re.IGNORECASE)
    if exp_match:
        try:
            experience_years = float(exp_match.group(1))
        except ValueError:
            experience_years = 0.0
            
    # Simple section parser for projects/certifications
    lines = raw_text.split("\n")
    current_section = None
    certifications = []
    
    for line in lines:
        l_str = line.strip()
        if re.match(r'^(projects|academic projects|key projects)', l_str, re.IGNORECASE):
            current_section = "projects"
            continue
        elif re.match(r'^(certifications|certificates|courses)', l_str, re.IGNORECASE):
            current_section = "certifications"
            continue
        elif re.match(r'^(education|skills|experience|work history)', l_str, re.IGNORECASE):
            current_section = None
            continue
            
        if current_section == "projects" and len(l_str) > 5:
            projects.append(l_str)
        elif current_section == "certifications" and len(l_str) > 5:
            certifications.append(l_str)

    return {
        "candidate_id": re.sub(r'[^a-zA-Z0-9]', '_', filename.lower()) if filename else "cand_01",
        "filename": filename,
        "name": name,
        "raw_text": raw_text,
        "skills": skills,
        "education": education,
        "projects": projects[:5],
        "certifications": certifications[:5],
        "experience_years": experience_years
    }

def parse_jd_content(raw_text: str, title: str = "Job Position") -> Dict[str, Any]:
    """Parses raw Job Description text into structured requirements."""
    skills = extract_skills(raw_text)
    education = extract_education(raw_text)
    
    return {
        "title": title,
        "raw_text": raw_text,
        "required_skills": skills,
        "required_education": education if education else ["B.Tech / B.E. / BCA / M.Tech"]
    }
