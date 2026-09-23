import os
import re
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config import BASE_DIR, SAMPLE_JDS_DIR, SAMPLE_RESUMES_DIR
from backend.resume_parser import extract_text_from_pdf, parse_resume_content, parse_jd_content
from backend.ranking_service import ranking_service
from backend.evaluation import evaluation_module
from backend.nlp_llm_service import llm_service
from backend.database import init_db, get_db
from backend.models import JobDescription, RecruitmentSession, Candidate, ScreeningResult

app = FastAPI(
    title="LLM-Powered Resume Screening API",
    description="Campus placement candidate screening & talent matching engine",
    version="1.0.0"
)

MAX_TOTAL_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB upload batch limit

@app.on_event("startup")
def startup_event():
    init_db()

# Enable CORS for local development & production deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class CreateSessionRequest(BaseModel):
    jd_title: str
    jd_text: str
    company: Optional[str] = "Company"
    session_name: Optional[str] = None
    mode: Optional[str] = "persistent"

def get_or_create_session(
    db: Session,
    jd_title: str,
    jd_text: str,
    company: Optional[str] = None,
    session_name: Optional[str] = None,
    mode: str = "persistent",
    session_id: Optional[str] = None
) -> Tuple[JobDescription, RecruitmentSession]:
    """Helper to locate or create JobDescription and RecruitmentSession."""
    clean_title = jd_title.strip() if jd_title else "Job Position"
    clean_text = jd_text.strip() if jd_text else ""
    clean_company = company.strip() if company else "Company"

    if session_id:
        sess = db.query(RecruitmentSession).filter(RecruitmentSession.id == session_id).first()
        if sess:
            jd = sess.job_description
            if mode:
                sess.mode = mode
                db.commit()
            return jd, sess

    # Find or create JD
    parsed_jd = parse_jd_content(clean_text, title=clean_title)
    jd = db.query(JobDescription).filter(
        JobDescription.jobTitle == clean_title,
        JobDescription.description == clean_text
    ).first()

    if not jd:
        jd = JobDescription(
            jobTitle=clean_title,
            company=clean_company,
            description=clean_text,
            requiredSkills=parsed_jd.get("required_skills", []),
            preferredSkills=parsed_jd.get("required_education", [])
        )
        db.add(jd)
        db.commit()
        db.refresh(jd)

    s_name = session_name.strip() if session_name and session_name.strip() else f"{clean_company}_{clean_title}".replace(" ", "_")
    
    sess = db.query(RecruitmentSession).filter(
        RecruitmentSession.jobDescriptionId == jd.id,
        RecruitmentSession.sessionName == s_name
    ).first()

    if not sess:
        sess = RecruitmentSession(
            jobDescriptionId=jd.id,
            company=clean_company,
            sessionName=s_name,
            mode=mode or "persistent"
        )
        db.add(sess)
        db.commit()
        db.refresh(sess)
    elif mode:
        sess.mode = mode
        db.commit()

    return jd, sess

def persist_and_rerank_session(
    db: Session,
    jd: JobDescription,
    sess: RecruitmentSession,
    new_parsed_resumes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Saves new parsed candidate resumes into DB tied to `sess.id`,
    fetches ALL candidates in that session, re-ranks the complete candidate pool together,
    updates ScreeningResults in DB, and returns sorted rankings.
    """
    # 1. Insert new candidates into DB with unique UUIDs, avoiding duplicate resumes
    existing_cands = db.query(Candidate).filter(Candidate.sessionId == sess.id).all()

    def normalize_str(s: str) -> str:
        s = re.sub(r'\(\d+\)', '', s or '')  # strip copy suffixes like (1), (2)
        s = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
        return s

    existing_filenames = {normalize_str(c.resumeFileName) for c in existing_cands if c.resumeFileName}
    existing_names = {normalize_str(c.name) for c in existing_cands if c.name}

    for parsed in new_parsed_resumes:
        raw_filename = parsed.get("filename", "PDF Resume")
        cand_name = parsed.get("name", "Candidate")

        norm_filename = normalize_str(raw_filename)
        norm_name = normalize_str(cand_name)

        # Check if this exact file or candidate name already exists in this session
        if norm_filename in existing_filenames or (norm_name != "unknowncandidate" and norm_name in existing_names):
            existing_cand = next((c for c in existing_cands if normalize_str(c.resumeFileName) == norm_filename or (normalize_str(c.name) == norm_name and norm_name != "unknowncandidate")), None)
            if existing_cand:
                existing_cand.resumeText = parsed.get("raw_text", existing_cand.resumeText)
                existing_cand.extractedSkills = parsed.get("skills", existing_cand.extractedSkills)
                existing_cand.education = parsed.get("education", existing_cand.education)
                existing_cand.experience = float(parsed.get("experience_years", existing_cand.experience))
                continue

        cand_db = Candidate(
            sessionId=sess.id,
            name=cand_name,
            resumeFileName=raw_filename,
            resumeText=parsed.get("raw_text", ""),
            education=parsed.get("education", []),
            experience=float(parsed.get("experience_years", 0.0)),
            extractedSkills=parsed.get("skills", []),
            projects=parsed.get("projects", []),
            certifications=parsed.get("certifications", [])
        )
        db.add(cand_db)
        existing_filenames.add(norm_filename)
        existing_names.add(norm_name)

    db.commit()

    # 2. Fetch ALL candidates belonging to this recruitment session
    all_cands_db = db.query(Candidate).filter(Candidate.sessionId == sess.id).all()

    all_parsed = []
    for cand in all_cands_db:
        parsed_dict = {
            "candidate_id": cand.id,
            "filename": cand.resumeFileName or "PDF Resume",
            "name": cand.name or "Candidate",
            "raw_text": cand.resumeText or "",
            "skills": cand.extractedSkills or [],
            "education": cand.education or [],
            "projects": cand.projects or [],
            "certifications": cand.certifications or [],
            "experience_years": cand.experience or 0.0
        }
        all_parsed.append(parsed_dict)

    # 3. Compute rankings across ALL candidates in the session
    parsed_jd = parse_jd_content(jd.description, title=jd.jobTitle)
    results = ranking_service.rank_candidates(parsed_jd, all_parsed)

    # 4. Update ScreeningResults in DB for all candidates in session
    db.query(ScreeningResult).filter(ScreeningResult.sessionId == sess.id).delete()

    for res in results:
        cand_id = res.get("candidate_id")
        breakdown = res.get("scores_breakdown", {})
        screening_db = ScreeningResult(
            jobDescriptionId=jd.id,
            sessionId=sess.id,
            candidateId=cand_id,
            overallMatchScore=float(res.get("overall_match_percentage", 0)),
            semanticSimilarityScore=float(breakdown.get("semantic_similarity", 0)),
            skillMatchScore=float(breakdown.get("skill_match", breakdown.get("skill_coverage", 0))),
            educationScore=float(breakdown.get("education", breakdown.get("qualification_match", 0))),
            experienceScore=float(breakdown.get("experience", 0)),
            matchingSkills=res.get("matching_skills", []),
            missingSkills=res.get("missing_skills", []),
            explanation=res.get("explanation", ""),
            rank=int(res.get("rank", 1))
        )
        db.add(screening_db)
    db.commit()

    return results

@app.get("/api/health")
def health_check():
    engine_name = "LLM + Semantic Matching" if llm_service.gemini_available else "Offline NLP Rule Engine"
    return {
        "status": "healthy",
        "llm_engine": engine_name,
        "is_llm_available": llm_service.gemini_available,
        "embedding_engine": "TF-IDF N-gram Cosine Similarity Vectorizer"
    }

@app.get("/api/sample-jds")
def get_sample_jds():
    """Retrieve pre-built sample job descriptions for easy demonstration."""
    samples = []
    if os.path.exists(SAMPLE_JDS_DIR):
        for file in os.listdir(SAMPLE_JDS_DIR):
            if file.endswith(".json"):
                path = SAMPLE_JDS_DIR / file
                with open(path, "r", encoding="utf-8") as f:
                    samples.append(json.load(f))
    return {"sample_jds": samples}

@app.get("/api/sample-resumes")
def get_sample_resumes():
    """Retrieve pre-built sample candidate resumes."""
    samples = []
    if os.path.exists(SAMPLE_RESUMES_DIR):
        for file in os.listdir(SAMPLE_RESUMES_DIR):
            if file.endswith(".json"):
                path = SAMPLE_RESUMES_DIR / file
                with open(path, "r", encoding="utf-8") as f:
                    samples.append(json.load(f))
    return {"sample_resumes": samples}

@app.get("/api/sessions")
def get_all_sessions(db: Session = Depends(get_db)):
    """List all recruitment screening sessions."""
    sessions = db.query(RecruitmentSession).order_by(RecruitmentSession.createdAt.desc()).all()
    res = []
    for s in sessions:
        total = db.query(Candidate).filter(Candidate.sessionId == s.id).count()
        res.append({
            "id": s.id,
            "session_name": s.sessionName,
            "company": s.company,
            "mode": s.mode,
            "jd_title": s.job_description.jobTitle if s.job_description else "Position",
            "jd_id": s.jobDescriptionId,
            "created_at": s.createdAt.isoformat() if s.createdAt else "",
            "total_candidates": total
        })
    return {"sessions": res}

@app.post("/api/sessions")
def create_session_endpoint(req: CreateSessionRequest, db: Session = Depends(get_db)):
    """Creates or retrieves a recruitment screening session."""
    if not req.jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description text cannot be empty.")
    jd, sess = get_or_create_session(
        db,
        jd_title=req.jd_title,
        jd_text=req.jd_text,
        company=req.company,
        session_name=req.session_name,
        mode=req.mode or "persistent"
    )
    return {
        "session_id": sess.id,
        "session_name": sess.sessionName,
        "company": sess.company,
        "mode": sess.mode,
        "jd_id": jd.id,
        "jd_title": jd.jobTitle,
        "required_skills": jd.requiredSkills or []
    }

@app.get("/api/sessions/{session_id}/rankings")
def get_session_rankings(session_id: str, db: Session = Depends(get_db)):
    """Fetch complete candidate rankings for a specific recruitment session."""
    sess = db.query(RecruitmentSession).filter(RecruitmentSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Recruitment session not found.")
    
    jd = sess.job_description
    results_db = db.query(ScreeningResult).filter(
        ScreeningResult.sessionId == session_id
    ).order_by(ScreeningResult.rank.asc()).all()

    rankings = []
    for res in results_db:
        cand = res.candidate
        rankings.append({
            "candidate_id": cand.id if cand else res.candidateId,
            "candidate_name": cand.name if cand else "Candidate",
            "filename": cand.resumeFileName if cand else "PDF Resume",
            "overall_match_percentage": int(res.overallMatchScore),
            "scores_breakdown": {
                "semantic_similarity": res.semanticSimilarityScore,
                "skill_coverage": res.skillMatchScore,
                "skill_match": res.skillMatchScore,
                "education": res.educationScore,
                "qualification_match": res.educationScore,
                "experience": res.experienceScore,
                "project_relevance": min(100.0, round(50.0 + (len(cand.extractedSkills or []) * 5.0), 1)) if cand else 60.0
            },
            "matching_skills": res.matchingSkills or [],
            "missing_skills": res.missingSkills or [],
            "education": cand.education if cand and cand.education else ["Bachelor's Degree"],
            "experience_years": cand.experience if cand else 0.0,
            "explanation": res.explanation or "",
            "rank": res.rank
        })

    return {
        "session_id": sess.id,
        "session_name": sess.sessionName,
        "company": sess.company,
        "mode": sess.mode,
        "jd_id": jd.id if jd else None,
        "jd_title": jd.jobTitle if jd else "Position",
        "jd_text": jd.description if jd else "",
        "required_skills": jd.requiredSkills if jd else [],
        "total_candidates": len(rankings),
        "rankings": rankings
    }

@app.get("/api/rankings/latest")
def get_latest_rankings(db: Session = Depends(get_db)):
    """Fetch the most recent recruitment session rankings from DB."""
    latest_sess = db.query(RecruitmentSession).order_by(RecruitmentSession.createdAt.desc()).first()
    if not latest_sess:
        return {
            "session_id": None,
            "session_name": None,
            "company": None,
            "mode": "persistent",
            "jd_id": None,
            "jd_title": "No position screened yet",
            "required_skills": [],
            "total_candidates": 0,
            "rankings": []
        }

    return get_session_rankings(latest_sess.id, db)

@app.post("/api/screen-resumes")
async def screen_resumes_endpoint(
    jd_title: str = Form(...),
    jd_text: str = Form(...),
    company: Optional[str] = Form("Company"),
    session_name: Optional[str] = Form(None),
    mode: Optional[str] = Form("persistent"),
    session_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Core screening endpoint: Accepts JD details and uploaded PDF resumes.
    Parses PDFs, appends candidates to the session pool, re-ranks ALL candidates, stores in DB, and returns complete rankings.
    """
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description text cannot be empty.")

    jd, sess = get_or_create_session(
        db,
        jd_title=jd_title,
        jd_text=jd_text,
        company=company,
        session_name=session_name,
        mode=mode or "persistent",
        session_id=session_id
    )

    parsed_resumes = []
    if files:
        total_size = 0
        for file in files:
            contents = await file.read()
            total_size += len(contents)
            
            if total_size > MAX_TOTAL_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Maximum upload size exceeded ({round(total_size / (1024*1024), 2)} MB uploaded, Limit: 10 MB). Please upload fewer or smaller files."
                )

            if len(contents) == 0:
                raise HTTPException(status_code=400, detail=f"File '{file.filename}' is empty. Please upload valid non-empty PDF files.")

            filename = file.filename or "resume.pdf"
            if not filename.lower().endswith(".pdf") and not contents.startswith(b"%PDF"):
                raise HTTPException(status_code=400, detail=f"File '{filename}' is not a valid PDF file. Please upload PDF format documents.")

            raw_text = extract_text_from_pdf(contents)
            if not raw_text.strip():
                raw_text = contents.decode("utf-8", errors="ignore")

            if not raw_text.strip():
                raise HTTPException(status_code=400, detail=f"Could not extract text from '{filename}'. The PDF file may be encrypted or corrupted.")

            parsed_cand = parse_resume_content(raw_text, filename=filename)
            parsed_resumes.append(parsed_cand)

    existing_count = db.query(Candidate).filter(Candidate.sessionId == sess.id).count()
    if not parsed_resumes and existing_count == 0:
        raise HTTPException(status_code=400, detail="No valid resume PDF files uploaded or existing in this session.")

    # Save new candidate resumes & re-rank ALL candidates in session
    results = persist_and_rerank_session(db, jd, sess, parsed_resumes)

    return {
        "session_id": sess.id,
        "session_name": sess.sessionName,
        "company": sess.company,
        "mode": sess.mode,
        "jd_id": jd.id,
        "jd_title": jd.jobTitle,
        "required_skills": jd.requiredSkills or [],
        "total_candidates": len(results),
        "rankings": results
    }

@app.post("/api/screen-sample-demo")
def screen_sample_demo(jd_id: Optional[str] = None, db: Session = Depends(get_db)):
    """1-Click Demo Endpoint: Screens built-in sample candidates against selected sample JD in a demo session."""
    jd_path = SAMPLE_JDS_DIR / "sde.json"
    jd_json = None

    if os.path.exists(jd_path):
        try:
            with open(jd_path, "r", encoding="utf-8") as f:
                jd_json = json.load(f)
        except Exception:
            pass

    if not jd_json and os.path.exists(SAMPLE_JDS_DIR):
        try:
            json_files = [f for f in os.listdir(SAMPLE_JDS_DIR) if f.endswith(".json")]
            if json_files:
                with open(SAMPLE_JDS_DIR / json_files[0], "r", encoding="utf-8") as f:
                    jd_json = json.load(f)
        except Exception:
            pass

    if not jd_json:
        jd_json = {
            "title": "Software Development Engineer (SDE-1)",
            "text": "Looking for a Software Development Engineer proficient in Python, C++, Data Structures, Algorithms, SQL, Docker, and REST APIs."
        }

    jd, sess = get_or_create_session(
        db,
        jd_title=jd_json.get("title", "Software Engineer"),
        jd_text=jd_json.get("text", "Software Engineer Job Description"),
        company="Tech Corp",
        session_name="Demo_SoftwareEngineer_Drive",
        mode="temporary"
    )

    # Check if demo candidates already exist to avoid duplication
    if db.query(Candidate).filter(Candidate.sessionId == sess.id).count() == 0:
        parsed_resumes = []
        if os.path.exists(SAMPLE_RESUMES_DIR):
            for file in os.listdir(SAMPLE_RESUMES_DIR):
                if file.endswith(".json"):
                    try:
                        with open(SAMPLE_RESUMES_DIR / file, "r", encoding="utf-8") as f:
                            cand_data = json.load(f)
                            parsed_resumes.append(parse_resume_content(cand_data["raw_text"], filename=cand_data["name"]))
                    except Exception:
                        pass
        
        if not parsed_resumes:
            parsed_resumes = [
                parse_resume_content("Rahul Verma. B.Tech Computer Science 2024. Skills: Python, C++, SQL, Algorithms, Docker, Git.", filename="Rahul_Verma_Resume.pdf"),
                parse_resume_content("Priya Sharma. M.Tech Artificial Intelligence 2024. Skills: Python, Machine Learning, NLP, TensorFlow, PyTorch, SQL.", filename="Priya_Sharma_Resume.pdf"),
                parse_resume_content("Amit Patel. BCA 2024. Skills: JavaScript, TypeScript, React, Node.js, HTML, CSS, SQL.", filename="Amit_Patel_Resume.pdf"),
                parse_resume_content("Neha Gupta. B.Tech IT 2024. Skills: Java, SQL, Selenium, Software Testing, Git.", filename="Neha_Gupta_Resume.pdf"),
                parse_resume_content("Vikram Singh. B.Tech Mechanical 2023. Skills: AutoCAD, SolidWorks, MATLAB.", filename="Vikram_Singh_Resume.pdf")
            ]

        results = persist_and_rerank_session(db, jd, sess, parsed_resumes)
    else:
        results = get_session_rankings(sess.id, db)["rankings"]

    return {
        "session_id": sess.id,
        "session_name": sess.sessionName,
        "company": sess.company,
        "mode": sess.mode,
        "jd_id": jd.id,
        "jd_title": jd.jobTitle,
        "required_skills": jd.requiredSkills or [],
        "total_candidates": len(results),
        "rankings": results
    }

@app.post("/api/sessions/{session_id}/clear")
def clear_session_endpoint(session_id: str, db: Session = Depends(get_db)):
    """Clears all candidates and rankings for the specified recruitment session."""
    sess = db.query(RecruitmentSession).filter(RecruitmentSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Recruitment session not found.")
    
    db.query(ScreeningResult).filter(ScreeningResult.sessionId == session_id).delete()
    db.query(Candidate).filter(Candidate.sessionId == session_id).delete()
    db.delete(sess)
    db.commit()

    return {"status": "success", "message": f"Recruitment session '{sess.sessionName}' cleared successfully."}

@app.delete("/api/sessions/clear-all")
def clear_all_sessions_endpoint(db: Session = Depends(get_db)):
    """Permanently clears ALL recruitment session data across the database."""
    db.query(ScreeningResult).delete()
    db.query(Candidate).delete()
    db.query(RecruitmentSession).delete()
    db.query(JobDescription).delete()
    db.commit()

    return {"status": "success", "message": "All recruitment screening data cleared successfully."}

@app.get("/api/evaluation")
def run_evaluation_benchmark():
    """Runs evaluation benchmark against test dataset and returns accuracy metrics."""
    return evaluation_module.evaluate_benchmark()

# Serve static frontend files
FRONTEND_DIR = BASE_DIR / "frontend"
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def read_root():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
