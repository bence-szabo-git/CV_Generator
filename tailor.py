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
# STEP 2 — AI TAILORING
# =============================================================

def tailor_cv(master_cv: dict, job_description: str) -> TailoredOutput | None:
    """Sends summary + experience to the AI for tailoring.
    Static sections (education, languages, skills, awards) are
    never sent to the AI — they pass through untouched in Step 3.
    """

    # Only send what the AI is allowed to touch
    ai_input = {
        "base_summary": master_cv.get("base_summary"),
        "experience": master_cv.get("experience")
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert CV tailor. "
                "Never invent facts, skills, or experience. "
                "Only reword and reorder existing content to match the job description. "
                "Output ONLY valid JSON — no preamble, no markdown, no backticks."
            )
        },
        {
            "role": "user",
            "content": f"""
MASTER CV DATA:
{json.dumps(ai_input, ensure_ascii=False, indent=2)}

JOB DESCRIPTION:
{job_description}

TASK:
1. Write a punchy 2-3 sentence tailored summary based on base_summary.
2. For each company in experience, keep the same company/description/logo_path/roles structure.
   Only reword bullet points to better match the job description keywords.
   Do NOT add new bullets. Do NOT invent skills.

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

    education = master_cv.get("education", [])

    # Restore logo_path from master_cv — never trust AI output for file paths
    master_logo_map = {
        job["company"]: job.get("logo_path", "")
        for job in master_cv.get("experience", [])
    }
    experience = [e.model_dump() for e in tailored.tailored_experience]
    for job in experience:
        job["logo_path"] = master_logo_map.get(job["company"], "")

    return {
        "tailored_summary": tailored.tailored_summary,
        "experience":        experience,
        "contact":           contact,
        "extracurricular":   master_cv.get("extracurricular", []),
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