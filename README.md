# LLM-Powered Resume Screening and Talent Matching Platform for Campus Placements

> **Academic Semester Project & External Review Prototype**  
> A realistic, explainable NLP/LLM candidate evaluation system designed for campus recruitment drives.

---

## 1. Project Overview
During campus placements, recruiters receive hundreds of candidate resumes for diverse technical positions. Traditional ATS engines rely on crude keyword searches that fail to capture semantic intent, contextual project depth, or soft skill nuances. 

This project delivers an **LLM-Powered Resume Screening & Talent Matching Platform** that extracts candidate information, computes vector embeddings and cosine similarity against Job Descriptions (JDs), ranks candidates using a transparent multi-factor scoring formula, and provides human-understandable (explainable) match rationales for recruiters.

---

## 2. Problem Statement
- **High Resume Volume**: Placement cells and recruiters struggle to manually review 500+ student resumes within short campus drive windows.
- **Black-Box AI Decisions**: Traditional keyword-matching tools score resumes without explaining *why* a student received a specific rank.
- **Misalignment & Keyword Stuffing**: Simple regex filters penalize candidates using synonyms (e.g., "Deep Learning" vs. "Neural Networks") while favoring candidates who overload buzzwords.

---

## 3. Objectives
1. **Automated PDF Parsing**: Extract candidate text, education, technical skills, projects, and experience from PDF resumes.
2. **Semantic Vector Matching**: Generate term embeddings and compute Cosine Similarity between JD requirements and candidate profiles.
3. **Multi-Factor Weighted Ranking**: Combine Semantic Similarity ($50\%$), Required Skill Coverage ($35\%$), and Educational Qualification ($15\%$).
4. **Explainable AI (XAI)**: Generate clear, recruiter-friendly rationales detailing Match %, Matching Skills, Missing Skills, and qualitative reasoning.
5. **Robust Dual Engine**: Support cloud LLM APIs (Google Gemini API) with a deterministic offline NLP fallback to ensure $100\%$ uptime during live demos.
6. **Empirical Evaluation**: Evaluate ranking quality against a manually labeled test dataset using Precision, Recall, F1-Score, and Top-K Accuracy.

---

## 4. System Architecture

```
                                  ┌────────────────────────┐
                                  │   Recruiter Web UI     │
                                  └───────────┬────────────┘
                                              │ Upload PDF Resumes & JD
                                              ▼
                                  ┌────────────────────────┐
                                  │ FastAPI Backend Server │
                                  └───────────┬────────────┘
                                              │
        ┌─────────────────────────────────────┼─────────────────────────────────────┐
        │                                     │                                     │
        ▼                                     ▼                                     ▼
┌───────────────┐                   ┌───────────────────┐                 ┌───────────────────┐
│ PDF Parser    │                   │ Embedding Engine  │                 │ NLP / LLM Service │
│ (pypdf/regex) │                   │ (TF-IDF/Cosine)   │                 │ (Gemini/Fallback) │
└───────┬───────┘                   └─────────┬─────────┘                 └─────────┬─────────┘
        │ Extracted Entities                  │ Vector Similarity                   │ Rationale
        └───────────────────┬─────────────────┘                                     │
                            ▼                                                       │
               ┌────────────────────────┐                                           │
               │ Weighted Rank Engine   │◄──────────────────────────────────────────┘
               │ (Semantic+Skill+Edu)   │
               └───────────┬────────────┘
                           │ Ranked Leaderboard & XAI Cards
                           ▼
               ┌────────────────────────┐
               │ Recruiter Dashboard UI │
               └────────────────────────┘
```

---

## 5. Technologies Used
- **Backend Framework**: Python 3.14, FastAPI, Uvicorn
- **PDF Extraction**: `pypdf`, `reportlab` (synthetic sample PDF generation)
- **NLP & Machine Learning**: `scikit-learn` (TF-IDF Vectorizer, Cosine Similarity), `numpy`
- **LLM Integration**: Google Gemini API (`google-generativeai`), with offline rule-based fallback
- **Frontend User Interface**: HTML5, CSS3 (Vanilla Dark Glassmorphism Design System), JavaScript (ES6 fetch API, Modals, Tab System)
- **Configuration & Environment**: `python-dotenv`, Pydantic

---

## 6. Installation Steps

### Prerequisites
- Python 3.10+ installed on your system.
- Git (optional).

### Step 1: Clone or Navigate to Project Directory
```bash
cd LLM-RESUME
```

### Step 2: Create & Activate Virtual Environment (Recommended)
```bash
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables (Optional)
Create or edit the `.env` file in the root directory:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```
*(If omitted, the platform automatically utilizes its built-in offline NLP engine).*

---

## 7. How to Run the Project

### Step 1: Generate Sample Data (One-Time Setup)
```bash
python generate_sample_pdfs.py
```

### Step 2: Start the Application
```bash
python run.py
```
*The web dashboard will automatically open in your default browser at `http://127.0.0.1:8000`.*

---

## 8. Dataset & Sample Data
The project includes realistic synthetic campus placement sample data:
- **Sample Job Descriptions**:
  1. `Software Development Engineer (SDE-1)`
  2. `Data Scientist / Machine Learning Engineer`
  3. `Full Stack Web Developer`
- **Sample Candidate PDF Resumes**:
  - `Rahul Verma`: High match candidate for SDE role (Python, FastAPI, C++, Docker, Data Structures).
  - `Priya Sharma`: High match candidate for Data Science role (PyTorch, TensorFlow, Scikit-Learn, NLP).
  - `Amit Patel`: High match candidate for Full Stack Developer role (React, Node.js, Express, MongoDB).
  - `Neha Gupta`: Medium match candidate (QA & Manual Testing background).
  - `Vikram Singh`: Low match candidate (Mechanical CAD background).

---

## 9. Matching Methodology
The candidate suitability score is computed using a 3-factor composite formula:

$$\text{Final Score} = (W_{\text{sem}} \cdot S_{\text{semantic}}) + (W_{\text{skill}} \cdot S_{\text{skill}}) + (W_{\text{edu}} \cdot S_{\text{qualification}})$$

Where:
- $W_{\text{sem}} = 0.50$ (Semantic Vector Similarity via Cosine Similarity)
- $W_{\text{skill}} = 0.35$ (Ratio of JD Required Skills present in candidate resume)
- $W_{\text{edu}} = 0.15$ (Degree level & educational qualification match score)

---

## 10. Cosine Similarity Explanation
Cosine Similarity measures the cosine of the angle between two multi-dimensional text vectors ($\vec{A}$ for Job Description and $\vec{B}$ for Resume).

$$\text{Cosine Similarity}(\vec{A}, \vec{B}) = \frac{\vec{A} \cdot \vec{B}}{\|\vec{A}\| \|\vec{B}\|} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}}$$

- Value of $1.0$ ($100\%$): Identical orientation / perfect semantic overlap.
- Value of $0.0$ ($0\%$): Complete orthogonality / no shared context.

---

## 11. LLM Usage
- **Role**: Synthesizes structured candidate entities and generates qualitative 2-sentence match rationales explaining why a candidate received their score.
- **Provider**: Google Gemini API (`gemini-1.5-flash`).
- **Resilience**: If the API key is unconfigured, rate-limited, or internet access is lost, the platform falls back to an offline heuristic template engine.

---

## 12. Evaluation Methodology
The evaluation module benchmarks predictions against a manually annotated ground-truth test dataset (`evaluation_dataset.json`):
- **Precision**: Ratio of true relevant candidates among predicted top matches.
- **Recall**: Proportion of ground-truth relevant candidates retrieved.
- **F1-Score**: Harmonic mean of Precision and Recall.
- **Top-1 Accuracy**: Percentage of test jobs where the model's #1 ranked candidate matched the human expert's top candidate.
- **Top-3 Accuracy**: Percentage of test jobs where the ground-truth top candidate appeared within the model's top 3 recommendations.

---

## 13. Limitations
- **Format Reliance**: Resume parsing depends on standard text layer presence in PDFs (scanned image PDFs require an OCR pre-processor).
- **Domain Focus**: Skill taxonomy is currently tuned for IT/Software and Engineering campus placement roles.

---

## 14. Out-of-Scope Features
*(Reserved as Future Enhancements)*:
1. Video or behavioral interview analysis.
2. Direct integration with commercial enterprise ATS systems (Workday, Greenhouse, Taleo).
3. Automated salary negotiation or offer-letter workflow management.

---

## 15. Future Enhancements
- Integration of Tesseract OCR for scanned image PDFs.
- Fine-tuned Sentence-BERT (SBERT) models customized on placement history data.
- Multi-lingual resume parsing support.
- Automated email dispatch for candidate interview scheduling.
