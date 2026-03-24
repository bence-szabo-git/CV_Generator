# =============================================================
# tailor.py
# 1. Loads master_cv.yaml + job_description.txt
# 2. Calls AI to tailor summary and experience bullets
# 3. Validates AI output with Pydantic
# 4. Merges AI output with static data
# 5. Writes resume_data.json (consumed by resume_template.typ)
# 6. Compiles PDF via Typst
# =============================================================

import os
import json
import shutil
import subprocess

import yaml
from pydantic import BaseModel, ValidationError
from huggingface_hub import InferenceClient

# --- Config ---
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
TEMPLATE_PATH = "templates/resume_template.typ"
DATA_OUTPUT_PATH = "templates/resume_data.json"
PDF_OUTPUT_PATH = "output/tailored_cv.pdf"

# --- AI Client ---
HF_TOKEN = os.getenv("LLM_API_KEY")
if not HF_TOKEN:
    raise ValueError("LLM_API_KEY not found. Ensure it is set in Codespace Secrets.")

client = InferenceClient(api_key=HF_TOKEN)


# =============================================================
# PYDANTIC MODELS — validates AI output before touching the PDF
# =============================================================

class TailoredRole(BaseModel):
    role: str
    location: str
    dates: str
    bullets: list[str]

class TailoredExperience(BaseModel):
    company: str
    description: str
    logo_path: str = ""
    roles: list[TailoredRole]

class TailoredOutput(BaseModel):
    tailored_summary: str
    tailored_experience: list[TailoredExperience]


# =============================================================
# STEP 1 — LOAD DATA
# =============================================================

def load_data() -> tuple[dict, str]:
    with open("data/master_cv.yaml", "r", encoding="utf-8") as f:
        master_cv = yaml.safe_load(f)
    with open("data/job_description.txt", "r", encoding="utf-8") as f:
        job_description = f.read()
    return master_cv, job_description


# =============================================================
# STEP 1.5 — PARSE JOB DESCRIPTION
# =============================================================

def parse_job_description(job_description: str) -> dict:
    """Extracts structured information from the job description to guide tailoring.
    This helps the AI focus on relevant aspects without hallucinating.
    """
    import re
    
    jd_lower = job_description.lower()
    
    # Extract required skills: look for common tech/business skills
    skills = []
    common_skills = [
        'python', 'aws', 'react', 'javascript', 'java', 'docker', 'kubernetes', 'sql', 'nosql', 
        'machine learning', 'ai', 'data science', 'agile', 'scrum', 'leadership', 'management',
        'analytics', 'logistics', 'operations', 'finance', 'marketing', 'project management'
    ]
    for skill in common_skills:
        if skill in jd_lower:
            skills.append(skill.title())
    
    # Team context: extract team size or structure
    team_context = ""
    team_match = re.search(r'team of (\d+)', jd_lower)
    if team_match:
        team_context = f"team of {team_match.group(1)}"
    elif 'cross-functional' in jd_lower:
        team_context = "cross-functional team"
    elif 'individual contributor' in jd_lower:
        team_context = "individual contributor"
    
    # Key responsibilities: extract bullet points or key sentences
    lines = [line.strip() for line in job_description.split('\n') if line.strip()]
    responsibilities = []
    for line in lines:
        if line.startswith('-') or line.startswith('•') or any(keyword in line.lower() for keyword in ['responsibilities', 'duties', 'will', 'develop', 'manage', 'lead']):
            responsibilities.append(line.lstrip('-• '))
            if len(responsibilities) >= 5:  # limit to 5
                break
    
    # Preferred qualifications: look for "preferred", "nice to have", etc.
    preferred = []
    in_preferred = False
    for line in lines:
        if 'preferred' in line.lower() or 'nice to have' in line.lower() or 'plus' in line.lower():
            in_preferred = True
        elif in_preferred and (line.startswith('-') or line.startswith('•')):
            preferred.append(line.lstrip('-• '))
            if len(preferred) >= 3:
                break
    
    return {
        "raw_description": job_description,
        "required_skills": skills,
        "team_context": team_context,
        "key_responsibilities": responsibilities,
        "preferred_qualifications": preferred
    }


# =============================================================
# STEP 2 — AI TAILORING
# =============================================================

def tailor_cv(master_cv: dict, job_description: str) -> TailoredOutput | None:
    """Sends summary + experience to the AI for tailoring.
    Static sections (education, languages, skills, awards) are
    never sent to the AI — they pass through untouched in Step 3.
    """

    # Parse job description for structured guidance
    parsed_jd = parse_job_description(job_description)

    # Only send what the AI is allowed to touch
    ai_input = {
        "base_summary": master_cv.get("base_summary"),
        "experience": master_cv.get("experience")
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert CV tailor. Your goal is to make the CV more relevant to the job description "
                "while maintaining 100% truthfulness and accuracy.\n\n"
                "CRITICAL RULES:\n"
                "- NEVER introduce technologies, numbers, or responsibilities not present in the original CV.\n"
                "- NEVER invent facts, skills, or experience.\n"
                "- Only reword and reorder existing content to emphasize job-matching keywords.\n"
                "- If a bullet doesn't connect to the job, leave it unchanged.\n"
                "- Prefer reordering bullets by relevance over heavy rephrasing.\n"
                "- Use keywords from the job description that already appear in the CV bullets.\n\n"
                "GOOD EXAMPLE:\n"
                "[Add your own good example here: show original bullet → tailored bullet that emphasizes a job keyword without inventing anything]\n\n"
                "BAD EXAMPLE:\n"
                "[Add your own bad example here: show original bullet → bad tailoring that invents a new skill or exaggerates]\n\n"
                "Output ONLY valid JSON — no preamble, no markdown, no backticks."
            )
        },
        {
            "role": "user",
            "content": f"""
PARSED JOB DESCRIPTION:
{json.dumps(parsed_jd, ensure_ascii=False, indent=2)}

MASTER CV DATA:
{json.dumps(ai_input, ensure_ascii=False, indent=2)}

TASK:
1. Write a punchy 2-3 sentence tailored summary based on base_summary, emphasizing aspects that match the job's required skills and responsibilities.
2. For each company in experience, keep the EXACT SAME company/description/logo_path/roles structure from the input. INCLUDE ALL ROLES for each company — do not omit or combine any roles. Only reword bullet points to better match the job description keywords from the parsed JD, and reorder bullets within each role to prioritize those most relevant to the job's key responsibilities.

Output EXACTLY in this JSON format:
{{
  "tailored_summary": "...",
  "tailored_experience": [
    {{
      "company": "...",
      "description": "...",
      "logo_path": "...",
      "roles": [
        {{
          "role": "...",
          "location": "...",
          "dates": "...",
          "bullets": ["...", "..."]
        }}
      ]
    }}
  ]
}}
"""
        }
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=messages,
            max_tokens=1500
        )
        raw = response.choices[0].message.content

        # Strip any accidental markdown fences
        start = raw.find("{")
        end = raw.rfind("}") + 1
        cleaned = raw[start:end]

        parsed = json.loads(cleaned)
        validated = TailoredOutput(**parsed)
        return validated

    except json.JSONDecodeError as e:
        print(f"❌ AI returned invalid JSON: {e}")
        print(f"Raw output was:\n{raw}")
        return None

    except ValidationError as e:
        print(f"❌ AI output failed validation:\n{e}")
        return None

    except Exception as e:
        print(f"❌ Unexpected error during AI call: {e}")
        return None


# =============================================================
# STEP 3 — MERGE AI OUTPUT WITH STATIC DATA
# =============================================================

def build_resume_data(tailored: TailoredOutput, master_cv: dict) -> dict:
    """Combines AI-tailored fields with untouched static fields
    into a single dict that matches what resume_template.typ expects.
    Logo paths are always taken from master_cv — the AI doesn't know
    about local files and will overwrite them with empty strings.
    """

    contact = master_cv.get("contact", {})

    # --- ADDED: Extract the LinkedIn slug here ---
    full_linkedin = contact.get("linkedin", "")
    if full_linkedin:
        # Splits by '/' and takes the last item, creating the slug
        contact["linkedin_slug"] = full_linkedin.strip('/').split('/')[-1]
    else:
        contact["linkedin_slug"] = ""
    # ---------------------------------------------
    
    education = master_cv.get("education", [])

    # Restore logo_path from master_cv — never trust AI output for file paths
    master_logo_map = {
        job["company"]: job.get("logo_path", "")
        for job in master_cv.get("experience", [])
    }
    experience = [e.model_dump() for e in tailored.tailored_experience]
    for job in experience:
        job["logo_path"] = master_logo_map.get(job["company"], "")
        
        # Restore additional role metadata from master_cv
        master_job = next((mj for mj in master_cv.get("experience", []) if mj["company"] == job["company"]), None)
        if master_job:
            master_roles = {f"{mr['role']}_{mr['dates']}": mr for mr in master_job.get("roles", [])}
            for role in job["roles"]:
                key = f"{role['role']}_{role['dates']}"
                if key in master_roles:
                    # Add metadata fields, excluding bullets (which come from AI)
                    for k, v in master_roles[key].items():
                        if k not in ['bullets']:
                            role[k] = v

    return {
        "tailored_summary": tailored.tailored_summary,
        "experience":        experience,
        "contact":           contact,
        "academic":          master_cv.get("academic", []),
        "education":         education,
        "languages":         master_cv.get("languages", []),
        "skills":            master_cv.get("skills_inventory", {}),
        "awards":            master_cv.get("awards", []),
    }


# =============================================================
# STEP 4 — WRITE JSON + COMPILE PDF
# =============================================================

def compile_pdf(resume_data: dict) -> None:
    """Writes resume_data.json next to the template, then
    calls Typst to compile the final PDF.
    """

    # Write JSON where Typst can find it (same dir as template)
    with open(DATA_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(resume_data, f, ensure_ascii=False, indent=2)
    print(f"✅ resume_data.json written.")

    # Ensure output folder exists
    os.makedirs("output", exist_ok=True)

    # Find Typst binary
    typst_path = shutil.which("typst") or os.path.expanduser("~/.local/bin/typst")

    result = subprocess.run(
        [typst_path, "compile", "--root", ".", TEMPLATE_PATH, PDF_OUTPUT_PATH],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"✨ PDF generated: {PDF_OUTPUT_PATH}")
    else:
        print(f"❌ Typst compile error:\n{result.stderr}")


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":
    print("📄 Loading CV and job description...")
    master_cv, job_description = load_data()

    print("🤖 AI is tailoring your CV...")
    tailored = tailor_cv(master_cv, job_description)

    if tailored is None:
        print("❌ Tailoring failed. Aborting.")
        exit(1)

    print("🔗 Merging with static data...")
    resume_data = build_resume_data(tailored, master_cv)

    print("🖨️  Compiling PDF...")
    compile_pdf(resume_data)