import re
import streamlit as st
import pandas as pd
import pdfplumber

# -------------------------------------------------------------------
# Page Config & Custom Human-Crafted Styling
# -------------------------------------------------------------------
st.set_page_config(page_title="Career Assistant", layout="wide", initial_sidebar_state="expanded")

# Injected custom styling to give it a hand-coded, polished frontend look
st.markdown("""
    <style>
    /* Global Page Overrides */
    .stApp { background-color: #F8FAFC !important; }
    
    /* Typography & Titles */
    .dashboard-title { font-size: 2.25rem; font-weight: 800; color: #0F172A; letter-spacing: -0.025em; margin-bottom: 0.25rem; }
    .dashboard-subtitle { font-size: 1rem; color: #475569; margin-bottom: 2rem; font-weight: 400; }
    .section-heading { font-size: 1.25rem; font-weight: 700; color: #1E293B; margin-bottom: 1rem; padding-bottom: 0.25rem; border-bottom: 1px solid #E2E8F0; }
    
    /* Skill Badges */
    .skill-badge { 
        display: inline-block; 
        background-color: #F1F5F9;
        color: #334155; 
        padding: 0.4rem 0.8rem; 
        margin: 0.25rem; 
        border-radius: 8px; 
        font-weight: 600; 
        font-size: 0.8rem; 
        border: 1px solid #E2E8F0;
    }
    
    /* Human-designed Info Banners */
    .status-banner {
        background-color: #FFFFFF;
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #10B981;
        margin-bottom: 1.5rem;
    }
    .status-banner p { margin: 0; color: #334155; font-size: 0.95rem; }
    
    .filter-banner {
        background-color: #FFFFFF;
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #3B82F6;
        margin-bottom: 1.5rem;
    }
    .filter-banner p { margin: 0; color: #334155; font-size: 0.95rem; }
    
    /* Sleek Job Listing Cards */
    .job-card {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
    }
    
    .job-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; }
    .job-title { font-size: 1.15rem; font-weight: 700; color: #0F172A; text-decoration: none; }
    .score-container { text-align: right; background-color: #F8FAFC; padding: 0.35rem 0.75rem; border-radius: 8px; border: 1px solid #E2E8F0; }
    .score-label { font-size: 0.7rem; color: #64748B; font-weight: 700; text-transform: uppercase; display: block; }
    .score-value { font-size: 1rem; font-weight: 700; color: #2563EB; }
    
    /* Custom Styled Action Buttons */
    .button-link {
        display: inline-flex;
        align-items: center;
        background-color: #0F172A;
        color: #FFFFFF !important;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 0.85rem;
        transition: background-color 0.2s;
    }
    .button-link:hover { background-color: #1E293B; }
    
    /* Gap Analysis Styling */
    .analysis-container { background-color: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0; padding: 1rem; margin-top: 0.75rem; }
    .tag-match { display: inline-block; background-color: #DCFCE7; color: #15803D; font-size: 0.75rem; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 4px; margin-bottom: 0.5rem; }
    .tag-miss { display: inline-block; background-color: #FEE2E2; color: #B91C1C; font-size: 0.75rem; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 4px; margin-bottom: 0.5rem; }
    .skills-list { font-size: 0.85rem; color: #475569; margin: 0; line-height: 1.5; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# Taxonomy Definitions & Role Matrix
# -------------------------------------------------------------------
skills_map = {
    "Frontend": ["html", "css", "javascript", "react", "nextjs", "vue", "tailwind", "typescript", "angular", "redux", "sass", "bootstrap", "vite", "webpack"],
    "Backend": ["python", "django", "flask", "node.js", "express", "sql", "postgresql", "api", "mongodb", "rest api", "java", "springboot", "fastapi", "redis", "graphql", "celery", "postgres", "mysql"],
    "AI/ML & Data Science": ["pandas", "numpy", "machine learning", "ml", "ai", "tensorflow", "pytorch", "scikit-learn", "computer vision", "llms", "nlp", "tableau", "data analysis", "deep learning", "excel", "xgboost", "huggingface", "langchain", "opencv", "scipy", "matplotlib"],
    "DevOps & Cloud": ["aws", "docker", "kubernetes", "jenkins", "terraform", "ci/cd", "git", "k8s", "github actions", "ansible", "circleci", "helm", "containers", "prometheus", "grafana", "ec2", "s3", "lambda"]
}

role_blueprints = {
    "Backend": [
        {"title": "Backend Engineer", "keywords": "Backend Engineer OR Backend Developer", "req_skills": ["python", "django", "node.js", "sql", "api", "rest api"]},
        {"title": "Python Developer", "keywords": "Python Developer Django Flask", "req_skills": ["python", "django", "flask", "sql", "api"]},
        {"title": "Node.js Developer", "keywords": "NodeJS Developer Backend", "req_skills": ["node.js", "express", "javascript", "api", "mongodb"]},
        {"title": "Java Cloud Engineer", "keywords": "Java Backend Spring Boot", "req_skills": ["java", "springboot", "sql", "api", "aws"]},
        {"title": "API Developer", "keywords": "REST API Developer Backend", "req_skills": ["api", "rest api", "python", "node.js", "sql"]}
    ],
    "Frontend": [
        {"title": "Frontend Engineer", "keywords": "Frontend Engineer OR Frontend Developer", "req_skills": ["html", "css", "javascript", "react", "typescript"]},
        {"title": "React.js Developer", "keywords": "ReactJS Developer Frontend", "req_skills": ["javascript", "react", "redux", "html", "css"]},
        {"title": "UI Engineer", "keywords": "UI Developer TypeScript Tailwind", "req_skills": ["html", "css", "javascript", "tailwind", "typescript"]},
        {"title": "Next.js Web Developer", "keywords": "NextJS Developer JavaScript", "req_skills": ["javascript", "nextjs", "react", "html", "css"]},
        {"title": "Fullstack Web Developer", "keywords": "Fullstack Developer React Node", "req_skills": ["javascript", "react", "node.js", "html", "css", "sql"]}
    ],
    "AI/ML & Data Science": [
        {"title": "Machine Learning Engineer", "keywords": "Machine Learning Engineer ML", "req_skills": ["python", "machine learning", "ml", "tensorflow", "pytorch", "scikit-learn"]},
        {"title": "Data Scientist", "keywords": "Data Scientist Data Science", "req_skills": ["python", "pandas", "numpy", "data analysis", "machine learning", "sql"]},
        {"title": "AI Engineer", "keywords": "AI Engineer LLM NLP PyTorch", "req_skills": ["python", "ai", "llms", "nlp", "pytorch", "huggingface"]},
        {"title": "Computer Vision Engineer", "keywords": "Computer Vision Engineer OpenCV", "req_skills": ["python", "computer vision", "opencv", "deep learning", "pytorch"]},
        {"title": "Data Analyst", "keywords": "Data Analyst Python SQL Tableau", "req_skills": ["python", "data analysis", "sql", "tableau", "excel"]}
    ],
    "DevOps & Cloud": [
        {"title": "DevOps Engineer", "keywords": "DevOps Engineer CI/CD", "req_skills": ["aws", "docker", "kubernetes", "jenkins", "ci/cd", "git"]},
        {"title": "Cloud Infrastructure Architect", "keywords": "Cloud Engineer AWS Azure", "req_skills": ["aws", "terraform", "kubernetes", "git", "ci/cd"]},
        {"title": "Site Reliability Engineer (SRE)", "keywords": "SRE Systems Engineer Kubernetes", "req_skills": ["kubernetes", "docker", "aws", "prometheus", "grafana", "git"]},
        {"title": "Platform Engineer", "keywords": "Platform Engineer Docker Terraform", "req_skills": ["docker", "terraform", "kubernetes", "aws", "jenkins"]},
        {"title": "Automation Engineer", "keywords": "Automation Engineer Jenkins Git", "req_skills": ["jenkins", "git", "ci/cd", "docker", "python"]}
    ]
}

# -------------------------------------------------------------------
# Core Processing Logic
# -------------------------------------------------------------------
def extract_text_from_pdf(file):
    try:
        text_chunks = []
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_chunks.append(page_text)
        return " ".join(text_chunks).lower()
    except Exception:
        return ""

def extract_skills(text):
    found_skills = []
    if not text.strip():
        return found_skills
        
    for category, variants in skills_map.items():
        for v in variants:
            pattern = r'(?:^|[^a-zA-Z0-9_.\-])' + re.escape(v.lower()) + r'(?:$|[^a-zA-Z0-9_.\-])'
            if re.search(pattern, text):
                if v in ["ml", "ai", "nlp", "llms", "api", "rest api", "html", "css", "k8s"]:
                    found_skills.append(v.upper())
                elif v in ["scikit-learn", "node.js", "next.js", "github actions"]:
                    found_skills.append("Scikit-Learn" if v == "scikit-learn" else v.title())
                else:
                    found_skills.append(v.title()) 
                    
    return sorted(list(set(found_skills)))

def analyze_orientation(user_skills):
    user_skills_lowercase = [s.lower() for s in user_skills]
    scores = {}
    
    for category, domain_skills in skills_map.items():
        matched_count = sum(1 for s in user_skills_lowercase if s in domain_skills)
        scores[category] = matched_count
        
    primary_domain = max(scores, key=scores.get)
    if scores[primary_domain] == 0:
        return "General / Entry Level", scores
        
    return primary_domain, scores

# -------------------------------------------------------------------
# Sidebar Navigation Panel
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📁 Upload Center")
    uploaded_file = st.file_uploader("Select Resume (PDF Format)", type="pdf", label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### 🎯 Job Focus Mode")
    options = ["All / Match My Resume"] + list(skills_map.keys())
    user_interest = st.selectbox(
        "Choose matching filter:",
        options=options,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    analyze_btn = st.button("✨ Run Match Analysis", use_container_width=True)

# -------------------------------------------------------------------
# Layout Frame Setup
# -------------------------------------------------------------------
st.markdown('<div class="dashboard-title">Tech Resume Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">Analyze technical resumes and discover matching career opportunities.</div>', unsafe_allow_html=True)

if "analysis_state" not in st.session_state:
    st.session_state.analysis_state = None

if analyze_btn:
    if uploaded_file is not None:
        with st.spinner("Analyzing profile patterns..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            extracted_skills = extract_skills(raw_text)
            primary_domain, score_matrix = analyze_orientation(extracted_skills)
            
            st.session_state.analysis_state = {
                "skills": extracted_skills,
                "primary": primary_domain,
                "scores": score_matrix,
                "has_text": bool(raw_text.strip()),
                "chosen_focus": user_interest
            }
    else:
        st.warning("Please complete a resume PDF upload in the sidebar panel first.")

# -------------------------------------------------------------------
# Helper Function for Human-Designed Job Listing Cards
# -------------------------------------------------------------------
def render_job_card(role, user_skills):
    user_skills_lowercase = [s.lower() for s in user_skills]
    req_skills = role["req_skills"]
    
    matched = [s.upper() if len(s) <= 4 else s.title() for s in req_skills if s in user_skills_lowercase]
    missing = [s.upper() if len(s) <= 4 else s.title() for s in req_skills if s not in user_skills_lowercase]
    score = len(matched)
    
    query = f"{role['keywords']}".replace(" ", "%20")
    linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={query}"
    
    st.markdown(f"""
    <div class="job-card">
        <div class="job-header">
            <div>
                <div class="job-title">{role['title']}</div>
                <div style="margin-top: 0.5rem;">
                    <a class="button-link" href="{linkedin_url}" target="_blank">View Active Openings ↗</a>
                </div>
            </div>
            <div class="score-container">
                <span class="score-label">Skill Match</span>
                <span class="score-value">{score}/{len(req_skills)}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Render expanding gap section natively using clean column margins
    with st.expander("Show detailed skill gap profile"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<span class="tag-match">Possessed Core Skills</span>', unsafe_allow_html=True)
            st.markdown(f'<p class="skills-list">{", ".join(matched) if matched else "None identified."}</p>', unsafe_allow_html=True)
        with col_b:
            st.markdown('<span class="tag-miss">Missing Growth Areas</span>', unsafe_allow_html=True)
            st.markdown(f'<p class="skills-list">{", ".join(missing) if missing else "Fully covered! ✨"}</p>', unsafe_allow_html=True)
            
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# Dashboard Execution & UI Rendering
# -------------------------------------------------------------------
if st.session_state.analysis_state is not None:
    data = st.session_state.analysis_state
    chosen_focus = user_interest 
    
    # Grid Breakdown (1/3 profile analysis, 2/3 role lists)
    left_col, right_col = st.columns([1, 2], gap="large")
    
    with left_col:
        st.markdown('<div class="section-heading">Extracted Skill Matrix</div>', unsafe_allow_html=True)
        if data["skills"]:
            badges_html = "".join([f'<span class="skill-badge">{s}</span>' for s in data["skills"]])
            st.markdown(badges_html, unsafe_allow_html=True)
            
            st.markdown('<div class="section-heading" style="margin-top: 2rem;">Skill Density Profile</div>', unsafe_allow_html=True)
            chart_df = pd.DataFrame(list(data["scores"].items()), columns=["Domain", "Skills Count"]).set_index("Domain")
            st.sidebar.markdown("") # visual spacer spacer
            st.bar_chart(chart_df)
        else:
            if not data["has_text"]:
                st.error("Profile Read Error: Could not parse text tracking layers.")
            else:
                st.warning("No matched tech matrix skills found inside file text blocks.")

    with right_col:
        st.markdown('<div class="section-heading">Recommended Matching Pipelines</div>', unsafe_allow_html=True)
        
        if data["skills"]:
            primary = data["primary"]
            
            if chosen_focus == "All / Match My Resume":
                if primary == "General / Entry Level":
                    st.info("General development metrics located. Showing entry level development tracks below.")
                    target_jobs = role_blueprints["Backend"] + role_blueprints["Frontend"]
                else:
                    st.markdown(f"""
                    <div class="status-banner">
                        <p>🎯 <b>Automated Recommendation Mode:</b> Your profile exhibits maximum structural match density toward <b>{primary}</b>. Showing tailored pipelines.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    target_jobs = role_blueprints[primary]
            else:
                st.markdown(f"""
                <div class="filter-banner">
                    <p>🔍 <b>Active Filter Override:</b> Showing curated openings exclusively for <b>{chosen_focus}</b> pipelines.</p>
                </div>
                """, unsafe_allow_html=True)
                target_jobs = role_blueprints[chosen_focus]
            
            # Print core job cards
            for role in target_jobs:
                render_job_card(role, data["skills"])

            # --- OPTIONAL LOWER LEVEL SECTIONS ---
            st.markdown('<div class="section-heading" style="margin-top: 2.5rem;">Explore Other Industries</div>', unsafe_allow_html=True)
            with st.expander("Click to discover structural tracks outside active streams"):
                categories = list(role_blueprints.keys())
                tab1, tab2, tab3, tab4 = st.tabs(categories)
                tab_mapping = {tab1: categories[0], tab2: categories[1], tab3: categories[2], tab4: categories[3]}
                
                for tab, cat_name in tab_mapping.items():
                    with tab:
                        st.write("")
                        for optional_role in role_blueprints[cat_name]:
                            render_job_card(optional_role, data["skills"])
        else:
            st.caption("Awaiting document parsing matrix maps.")
else:
    st.info("💡 Complete a profile upload in the left panel to deploy the data dashboards.")