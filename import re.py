import re
import streamlit as st
import pandas as pd
from pypdf import PdfReader

# -------------------------------
# Configuration & Dataset
# -------------------------------
st.set_page_config(page_title="Universal Career Assistant", layout="wide")

@st.cache_data
def load_data():
    try:
        # Ensure 'jobs.csv' has columns: 'job_title' and 'skills_required'
        return pd.read_csv("jobs.csv")
    except FileNotFoundError:
        return None

jobs = load_data()

# -------------------------------
# SKILLS & INTERESTS MAP
# -------------------------------
skills_map = {
    "Frontend": ["html", "css", "javascript", "react", "nextjs", "vue", "tailwind", "typescript"],
    "Backend": ["python", "django", "flask", "node.js", "express", "sql", "postgresql", "api", "mongodb"],
    "Data Science": ["pandas", "numpy", "machine learning", "ml", "ai", "tensorflow", "pytorch"],
    "DevOps": ["aws", "docker", "kubernetes", "jenkins", "terraform", "ci/cd"],
    "Business/Other": ["management", "marketing", "sales", "communication", "excel"]
}

# -------------------------------
# Logic Functions
# -------------------------------
def extract_text_from_pdf(file):
    try:
        reader = PdfReader(file)
        text = " ".join([page.extract_text() or "" for page in reader.pages])
        return re.sub(r"\s+", " ", text).lower()
    except Exception as e:
        return ""

def extract_skills(text):
    found = []
    for category, variants in skills_map.items():
        for v in variants:
            # Custom boundary check to support special characters like 'node.js'
            pattern = r'(?:^|[^a-zA-Z0-9_.\-])' + re.escape(v.lower()) + r'(?:$|[^a-zA-Z0-9_.\-])'
            if re.search(pattern, text):
                if v == "ml": v = "Machine Learning"
                if v == "ai": v = "AI"
                found.append(v.title() if len(v) > 2 else v.upper()) 
    return sorted(list(set(found)))

def match_jobs(user_skills, jobs_df, user_interest):
    results = []
    user_skills_l = [s.lower() for s in user_skills]
    
    if jobs_df is not None:
        for _, row in jobs_df.iterrows():
            job_title = str(row["job_title"]).lower()
            job_skills = str(row["skills_required"]).lower()
            
            # Map selected interest to potential keywords in job titles
            interest_keywords = [user_interest.lower()]
            if user_interest == "Data Science":
                interest_keywords = ["data science", "data scientist", "machine learning", "analytics", "ml"]
            elif user_interest == "Backend":
                interest_keywords = ["backend", "back-end", "python developer", "java developer", "software engineer", "node"]
            elif user_interest == "Frontend":
                interest_keywords = ["frontend", "front-end", "ui", "ux", "web developer", "react"]

            if not any(kw in job_title for kw in interest_keywords):
                continue 
                
            score = sum(1 for skill in user_skills_l if skill in job_skills)
            if score > 0:
                results.append({"title": row["job_title"], "score": score})
    
    return sorted(results, key=lambda x: x['score'], reverse=True)[:5]

# -------------------------------
# UI & SESSION STATE
# -------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.title("📁 Document Center")
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
    
    user_interest = st.selectbox(
        "🎯 Select Your Career Interest Focus:",
        options=list(skills_map.keys())
    )
    
    analyze_btn = st.button("🚀 Analyze Now")

# Main Page Heading
st.title("🚀 Universal Career Assistant")
st.write("---")

# -------------------------------
# PROCESSING ACTION
# -------------------------------
if analyze_btn:
    if uploaded_file and jobs is not None:
        with st.spinner("Analyzing profile and matching positions..."):
            text = extract_text_from_pdf(uploaded_file)
            skills = extract_skills(text)
            matches = match_jobs(skills, jobs, user_interest)
            
            if skills:
                res_text = f"✅ **Skills found in resume:** {', '.join(skills)}\n\n🎯 **Focused Filter Applied:** Showing jobs matching **{user_interest}**."
                if not matches:
                    res_text += f"\n\n⚠️ No direct matches found for '{user_interest}' in our dataset. Try exploring broader matching titles directly via LinkedIn below!"
                    matches = [{"title": f"General {user_interest} Specialist", "score": 0}]
            else:
                res_text = "❌ No matching skills identified. Please ensure the PDF contains parseable text content."
                matches = []

            # Prepend to history so the newest analysis shows at the top
            st.session_state.history.insert(0, {
                "content": res_text,
                "skills": skills,
                "jobs": matches
            })
    elif jobs is None:
        st.error("Missing 'jobs.csv' file! Please ensure it resides in the same directory.")
    else:
        st.warning("Please upload a resume first.")

# -------------------------------
# RENDER OUTPUTS
# -------------------------------
if st.session_state.history:
    for idx, chat in enumerate(st.session_state.history):
        st.info(chat["content"])
        
        if chat.get("jobs"):
            st.subheader("🔍 Recommended Career Matches:")
            cols = st.columns(len(chat["jobs"]))
            
            for i, job in enumerate(chat["jobs"]):
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(Locally generated matches)
                        st.markdown(f"**{job['title']}**")
                        st.caption(f"Skill Match Points: {job['score']}")
                        
                        # Dynamic job link generation
                        search_query = f"{job['title']}".replace(" ", "%20")
                        link = f"https://www.linkedin.com/jobs/search/?keywords={search_query}"
                        st.markdown(f"[🔗 Find Job]({link})")
        st.write("---")
else:
    st.info("💡 Upload your resume PDF and click **Analyze Now** in the sidebar to view matched career paths.")