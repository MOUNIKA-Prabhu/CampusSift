import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = BASE_DIR / "sample_data"
JD_DIR = SAMPLE_DIR / "job_descriptions"
RESUME_DIR = SAMPLE_DIR / "sample_resumes"

JD_DIR.mkdir(parents=True, exist_ok=True)
RESUME_DIR.mkdir(parents=True, exist_ok=True)

# 1. Generate Sample Job Descriptions
jds = [
    {
        "id": "jd_sde",
        "title": "Software Development Engineer (SDE-1)",
        "department": "Engineering",
        "experience_required": "0-2 Years",
        "text": """Job Title: Software Development Engineer (SDE-1)
Location: Campus Hiring / Remote

About the Role:
We are looking for an energetic SDE-1 to join our backend engineering team.

Required Qualifications:
- Bachelor's degree in Computer Science, B.Tech, or B.E.
- Strong proficiency in Python, C++, SQL, and REST APIs.
- Experience with Git, Data Structures, Algorithms, and Docker.
- Knowledge of cloud services like AWS or GCP is a plus.
- Good understanding of Software Development Life Cycle (SDLC) and Agile methodologies.
"""
    },
    {
        "id": "jd_ds",
        "title": "Data Scientist / Machine Learning Engineer",
        "department": "AI & Analytics",
        "experience_required": "0-2 Years",
        "text": """Job Title: Data Scientist / Machine Learning Engineer
Location: Campus Hiring

About the Role:
We are seeking a Junior Data Scientist to build NLP models and predictive analytics pipelines.

Required Qualifications:
- B.Tech / M.Tech / M.S. in Computer Science, Data Science, or AI.
- Expertise in Python, TensorFlow, PyTorch, Scikit-Learn, and NLP.
- Strong knowledge of Data Analysis, Pandas, NumPy, Statistics, and SQL.
- Experience with Deep Learning, Computer Vision, and model deployment.
"""
    },
    {
        "id": "jd_fullstack",
        "title": "Full Stack Web Developer",
        "department": "Product Development",
        "experience_required": "0-2 Years",
        "text": """Job Title: Full Stack Web Developer
Location: Campus Hiring

About the Role:
Looking for a Full Stack Developer to craft web applications.

Required Qualifications:
- B.Tech / BCA / MCA in Information Technology or Computer Applications.
- Core skills: JavaScript, TypeScript, React, Node.js, Express, HTML, CSS, SQL, MongoDB.
- Experience with REST API design, Git, Docker, and frontend state management.
"""
    }
]

for jd in jds:
    with open(JD_DIR / f"{jd['id'].replace('jd_', '')}.json", "w", encoding="utf-8") as f:
        json.dump(jd, f, indent=2)

# 2. Sample Resumes Content
resumes = [
    {
        "name": "Rahul Verma",
        "email": "rahul.verma@example.com",
        "phone": "+91 9876543210",
        "education": "B.Tech in Computer Science, 2024 (GPA: 8.8/10)",
        "skills": ["Python", "C++", "SQL", "REST API", "Docker", "Git", "Data Structures", "FastAPI"],
        "projects": [
            "Microservices Billing System: Built using Python FastAPI, PostgreSQL, and Docker.",
            "Algorithm Visualizer: Web application built with JavaScript and Data Structures."
        ],
        "experience": "SDE Intern at TechCorp (6 Months): Developed backend APIs using Python and REST framework.",
        "certifications": ["AWS Certified Cloud Practitioner", "Python Backend Mastery"]
    },
    {
        "name": "Priya Sharma",
        "email": "priya.sharma@example.com",
        "phone": "+91 9876543211",
        "education": "M.Tech in Artificial Intelligence, 2024 (GPA: 9.1/10)",
        "skills": ["Python", "Machine Learning", "NLP", "PyTorch", "TensorFlow", "Scikit-Learn", "Pandas", "NumPy", "SQL"],
        "projects": [
            "Automated Sentiment Classifier: Fine-tuned BERT model for movie reviews with 94% accuracy.",
            "Resume Screening Engine: Applied TF-IDF and Cosine Similarity for document comparison."
        ],
        "experience": "AI Research Intern (5 Months): Implemented NLP transformers for document entity extraction.",
        "certifications": ["Deep Learning Specialization - Coursera", "TensorFlow Developer Certificate"]
    },
    {
        "name": "Amit Patel",
        "email": "amit.patel@example.com",
        "phone": "+91 9876543212",
        "education": "BCA / MCA, 2024 (GPA: 8.4/10)",
        "skills": ["JavaScript", "TypeScript", "React", "Node.js", "Express", "MongoDB", "HTML", "CSS", "REST API", "Git"],
        "projects": [
            "E-Commerce Web Portal: Fullstack app built with React, Node.js, Express, and MongoDB.",
            "Real-time Chat App: WebSockets and React frontend with JWT authentication."
        ],
        "experience": "Frontend Developer Intern (6 Months): Built responsive React components and integrated REST APIs.",
        "certifications": ["Full Stack Web Development Certification", "React Advanced Developer"]
    },
    {
        "name": "Neha Gupta",
        "email": "neha.gupta@example.com",
        "phone": "+91 9876543213",
        "education": "B.Tech in Information Technology, 2024 (GPA: 7.9/10)",
        "skills": ["Java", "SQL", "Selenium", "Manual Testing", "Git", "HTML", "Agile"],
        "projects": [
            "Automated E2E Test Suite: Developed Selenium test automation scripts for web portals.",
            "Bug Tracking Dashboard: HTML/CSS front-end portal for bug reporting."
        ],
        "experience": "QA Engineering Intern (4 Months): Executed test cases and performed regression testing.",
        "certifications": ["ISTQB Foundation Level Certification"]
    },
    {
        "name": "Vikram Singh",
        "email": "vikram.singh@example.com",
        "phone": "+91 9876543214",
        "education": "B.Tech in Mechanical Engineering, 2023 (GPA: 7.2/10)",
        "skills": ["AutoCAD", "SolidWorks", "MATLAB", "Thermodynamics", "Manufacturing"],
        "projects": [
            "Design of HVAC Cooling Tower: CAD modeling and thermal stress simulation in SolidWorks.",
            "Solar Panel Mounting Frame Optimization: Structural analysis."
        ],
        "experience": "Mechanical Apprentice (6 Months): Handled plant maintenance and machinery CAD design.",
        "certifications": ["Certified SolidWorks Professional (CSWP)"]
    }
]

# Generate JSON metadata and PDF files using ReportLab if available
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    has_reportlab = True
except ImportError:
    has_reportlab = False
    print("ReportLab not installed yet. Creating plain text formatted PDFs.")

for cand in resumes:
    filename_base = cand["name"].replace(" ", "_") + "_Resume"
    
    # Save raw text structured JSON
    raw_text = f"""{cand['name']}
Email: {cand['email']} | Phone: {cand['phone']}
Education: {cand['education']}

SKILLS:
{', '.join(cand['skills'])}

EXPERIENCE:
{cand['experience']}

PROJECTS:
""" + "\n".join([f"- {p}" for p in cand['projects']]) + f"\n\nCERTIFICATIONS:\n" + "\n".join([f"- {c}" for c in cand['certifications']])

    cand_json = dict(cand)
    cand_json["raw_text"] = raw_text
    with open(RESUME_DIR / f"{filename_base}.json", "w", encoding="utf-8") as f:
        json.dump(cand_json, f, indent=2)

    # Generate PDF file
    pdf_path = RESUME_DIR / f"{filename_base}.pdf"
    if has_reportlab:
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph(f"<b><font size=16 color='#1E293B'>{cand['name']}</font></b>", styles['Heading1']))
        story.append(Paragraph(f"<font size=10 color='#64748B'>{cand['email']} | {cand['phone']} | {cand['education']}</font>", styles['Normal']))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("<b>TECHNICAL SKILLS</b>", styles['Heading2']))
        story.append(Paragraph(", ".join(cand['skills']), styles['Normal']))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph("<b>WORK EXPERIENCE</b>", styles['Heading2']))
        story.append(Paragraph(cand['experience'], styles['Normal']))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph("<b>ACADEMIC PROJECTS</b>", styles['Heading2']))
        for p in cand['projects']:
            story.append(Paragraph(f"• {p}", styles['Normal']))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph("<b>CERTIFICATIONS</b>", styles['Heading2']))
        for c in cand['certifications']:
            story.append(Paragraph(f"• {c}", styles['Normal']))
            
        doc.build(story)
    else:
        # Fallback: create raw file
        with open(pdf_path, "wb") as f:
            f.write(raw_text.encode("utf-8"))

print("Sample JDs and candidate resumes successfully generated!")

# 3. Create Ground-Truth Evaluation Dataset
eval_dataset = [
    {
        "job_title": "Software Development Engineer (SDE-1)",
        "jd_text": jds[0]["text"],
        "ground_truth_top_candidate": "Rahul Verma",
        "candidates": [
            {
                "name": "Rahul Verma",
                "resume_text": json.load(open(RESUME_DIR / "Rahul_Verma_Resume.json"))["raw_text"],
                "ground_truth_relevant": True
            },
            {
                "name": "Priya Sharma",
                "resume_text": json.load(open(RESUME_DIR / "Priya_Sharma_Resume.json"))["raw_text"],
                "ground_truth_relevant": True
            },
            {
                "name": "Amit Patel",
                "resume_text": json.load(open(RESUME_DIR / "Amit_Patel_Resume.json"))["raw_text"],
                "ground_truth_relevant": True
            },
            {
                "name": "Neha Gupta",
                "resume_text": json.load(open(RESUME_DIR / "Neha_Gupta_Resume.json"))["raw_text"],
                "ground_truth_relevant": False
            },
            {
                "name": "Vikram Singh",
                "resume_text": json.load(open(RESUME_DIR / "Vikram_Singh_Resume.json"))["raw_text"],
                "ground_truth_relevant": False
            }
        ]
    },
    {
        "job_title": "Data Scientist / Machine Learning Engineer",
        "jd_text": jds[1]["text"],
        "ground_truth_top_candidate": "Priya Sharma",
        "candidates": [
            {
                "name": "Priya Sharma",
                "resume_text": json.load(open(RESUME_DIR / "Priya_Sharma_Resume.json"))["raw_text"],
                "ground_truth_relevant": True
            },
            {
                "name": "Rahul Verma",
                "resume_text": json.load(open(RESUME_DIR / "Rahul_Verma_Resume.json"))["raw_text"],
                "ground_truth_relevant": True
            },
            {
                "name": "Vikram Singh",
                "resume_text": json.load(open(RESUME_DIR / "Vikram_Singh_Resume.json"))["raw_text"],
                "ground_truth_relevant": False
            }
        ]
    }
]

with open(SAMPLE_DIR / "evaluation_dataset.json", "w", encoding="utf-8") as f:
    json.dump(eval_dataset, f, indent=2)

print("Evaluation dataset generated successfully!")
