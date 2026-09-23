# External Review & Viva Voce Q&A Guide

> **Project Title**: LLM-Powered Resume Screening and Talent Matching Platform for Campus Placements  
> **Target Speaking Time**: ~20–30 seconds per response.

---

### Q1. Why is this study needed?
**Answer:**  
"During campus placement drives, placement cells receive hundreds of student resumes within a very short timeframe. Manual screening is slow, inconsistent, and error-prone. Traditional ATS software relies on rigid keyword matching that penalizes qualified students using different terms. This project automates resume screening using NLP and LLMs to provide fast, objective, and explainable candidate rankings."

---

### Q2. Why use LLMs instead of traditional keyword matching?
**Answer:**  
"Traditional keyword matching only looks for exact word occurrences, missing context and synonyms—for instance, failing to connect 'Neural Networks' with 'Deep Learning'. LLMs understand semantic context, project descriptions, and domain nuances. They can extract structured entities accurately and generate human-readable explanations for why a candidate fits a role."

---

### Q3. Why use cosine similarity?
**Answer:**  
"Cosine similarity measures the angular difference between two high-dimensional text vectors, comparing direction rather than document length. This prevents long, wordy resumes from getting artificially high match scores simply due to volume. It provides a normalized score between 0% and 100% representing semantic alignment."

---

### Q4. Why do we need embeddings?
**Answer:**  
"Computers cannot directly compare raw text for contextual similarity. Embeddings convert text documents—such as Job Descriptions and candidate resumes—into dense numerical vector representations. Words with similar meanings end up close together in vector space, allowing mathematical calculation of semantic match."

---

### Q5. Why use a vector database?
**Answer:**  
"A vector database indexes high-dimensional embeddings to perform fast approximate nearest-neighbor (ANN) similarity searches across thousands of candidate profiles. It allows instant retrieval of the most relevant resumes for any given job description without scanning every single resume linearly."

---

### Q6. Is a vector database really necessary at prototype scale?
**Answer:**  
"At prototype scale with tens or hundreds of resumes, in-memory vector indexing using NumPy or Scikit-Learn TF-IDF matrices is sufficient, fast, and light on computing resources. However, for production scale with millions of candidates, a dedicated vector store like Milvus, Chroma, or FAISS becomes necessary for efficient sub-second search."

---

### Q7. What happens if the LLM API is down?
**Answer:**  
"Our architecture is designed with a resilient dual-engine strategy. If the cloud LLM API is offline or unreachable, the system automatically switches to an offline NLP rule-based fallback engine. It computes similarity and skill matching locally without interrupting the recruiter's workflow or breaking the system."

---

### Q8. What happens if the API is rate-limited?
**Answer:**  
"If the API returns a rate-limit error, the backend catches the exception gracefully and routes the request to our local deterministic rule engine. The user interface displays a status indicator notifying the user that fallback mode is active, ensuring uninterrupted demonstration and reliability."

---

### Q9. Why not fine-tune your own model?
**Answer:**  
"Fine-tuning a custom LLM requires massive labeled placement datasets, significant GPU infrastructure, high cost, and ongoing maintenance. For a college semester project, utilizing pre-trained embeddings combined with prompt engineering and LLM APIs provides superior semantic accuracy in a resource-efficient manner."

---

### Q10. What will this project actually cost to run?
**Answer:**  
"The prototype costs essentially zero dollars to run. It uses open-source Python libraries like Scikit-Learn and PyPDF locally, alongside free-tier API quotas (like Google Gemini API free tier). It runs efficiently on standard laptop hardware without requiring expensive GPU servers."

---

### Q11. What is your dataset?
**Answer:**  
"Our prototype uses a curated dataset of campus placement job descriptions (such as SDE, Data Scientist, and Full Stack Developer) along with candidate PDF resumes representing high, medium, and low qualification levels. We also built an evaluation dataset containing expert ground-truth annotations to test ranking accuracy."

---

### Q12. How will you evaluate accuracy?
**Answer:**  
"We evaluate accuracy by comparing predicted rankings against expert ground-truth labels. We measure classification metrics including Precision, Recall, and F1-score at a 50% match threshold. Additionally, we compute Top-1 and Top-3 Ranking Accuracy to ensure the best candidates appear at the top of the leaderboard."

---

### Q13. How do you prevent black-box decisions?
**Answer:**  
"Instead of displaying a single unexplainable number, our platform provides complete transparency. For every candidate, it breaks down the score into Semantic Match, Skill Coverage, and Qualifications. It explicitly displays Matching Skills, Missing Skills, and a plain-English explanation generated by the AI."

---

### Q14. What are the limitations?
**Answer:**  
"Current limitations include reliance on digital text PDFs (scanned image PDFs require an additional OCR module) and a technical skill taxonomy currently focused on IT and engineering roles. Also, evaluation is conducted on a campus-scale sample dataset rather than enterprise-scale data."

---

### Q15. What is out of scope?
**Answer:**  
"Out of scope for this prototype are: video or behavioral interview analysis, direct API integration with commercial enterprise ATS portals like Workday or Taleo, and automated salary negotiation workflows. These are preserved as future roadmap items."

---

### Q16. What are the future enhancements?
**Answer:**  
"Future enhancements include adding Tesseract OCR for scanned handwritten resumes, fine-tuning Sentence-BERT models on historical placement hiring decisions, supporting multi-lingual resume parsing, and adding automated email scheduling for shortlisted students."

---

### Q17. What is the role of each project component?
**Answer:**  
"The **FastAPI backend** handles API routing and business logic; the **Resume Parser** extracts text and entities from PDFs; the **Embedding Service** converts text to vectors and calculates Cosine Similarity; the **Ranking Engine** applies composite scoring weights; the **Explainability Module** generates skill gap rationales; and the **Frontend** provides an intuitive recruiter dashboard."

---

### Q18. How is candidate ranking calculated?
**Answer:**  
"Ranking is calculated using a weighted multi-factor formula: 50% weight for Semantic Vector Similarity (Cosine Similarity), 35% weight for Skill Match ratio (matching required JD skills), and 15% weight for Educational Qualification alignment. Candidates are sorted descending by this composite score."

---

### Q19. How is fairness/bias handled?
**Answer:**  
"The platform evaluates candidates strictly on verified skills, project technical descriptions, and educational qualifications. Personal demographic attributes such as gender, age, religion, or photo are intentionally excluded from the vector embedding and ranking calculations to promote objective screening."

---

### Q20. Can the system handle hundreds of resumes?
**Answer:**  
"Yes. In our prototype, batch processing and vector matrix operations allow screening 100+ PDF resumes in a few seconds. For scaling to thousands of resumes in enterprise settings, vector stores like Chroma or FAISS can be integrated to maintain sub-second retrieval times."
