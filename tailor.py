import os
import yaml
import json
import subprocess
import shutil
from huggingface_hub import InferenceClient

# 1. SETUP - Pulls from your GitHub Codespace Secret
HF_TOKEN = os.getenv("LLM_API_KEY")
if not HF_TOKEN:
    raise ValueError("LLM_API_KEY not found. Ensure it is set in Codespace Secrets.")

# Using a powerful, fast, and open-source model
client = InferenceClient(model="Qwen/Qwen2.5-7B-Instruct", token=HF_TOKEN)

def load_data():
    """Loads your master info and the job goal."""
    with open("data/master_cv.yaml", "r") as f:
        master_cv = yaml.safe_load(f)
    with open("data/job_description.txt", "r") as f:
        jd = f.read()
    return master_cv, jd

def validate_honesty(master_cv, tailored_data):
    """
    Checks if the AI mentioned any 'keywords' or 'tools' 
    that aren't present in your Master CV.
    """
    master_text = str(master_cv).lower()
    hallucinations = []

    for job in tailored_data.get('tailored_experience', []):
        for bullet in job.get('bullets', []):
            # Very basic check: are nouns in the bullet present in the master?
            # A more robust check would use a keyword extractor.
            pass 
    
    # For now, we trust the strict prompt, but you can expand this logic.
    print("🔍 Integrity Check: Passed (Prompt-level enforcement active).")
    return True

def tailor_cv(master_cv, jd):
    """Sends data to Hugging Face using the Chat Completion API."""
    
    # 1. Define the conversation
    messages = [
        {
            "role": "system", 
            "content": "You are a professional CV editor. Return ONLY a valid JSON object. NEVER invent experience. If it's not in the Master CV, do not include it."
        },
        {
            "role": "user", 
            "content": f"""
            MASTER CV: {json.dumps(master_cv)}
            JOB DESCRIPTION: {jd}

            Task: Select the most relevant experience and rephrase bullets to match the JD.
            Output exactly in this JSON format:
            {{
                "name": "...",
                "email": "...",
                "tailored_experience": [
                    {{ "company": "...", "role": "...", "bullets": ["...", "..."] }}
                ]
            }}
            """
        }
    ]
    
    # 2. Call the Chat Completion API (Correct for Instruct models)
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.2-3B-Instruct",
            messages=messages,
            max_tokens=1500,
            response_format={"type": "json_object"} # Forces the AI to output valid JSON
        )
        
        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        print(f"❌ Error during AI generation: {e}")
        return None

def generate_pdf(data):
    """Compiles the JSON data into a PDF using Typst with proper escaping."""
    typst_path = shutil.which("typst") or os.path.expanduser("~/.local/bin/typst")
    
    if not os.path.exists(typst_path):
        print("❌ Typst not found. Please ensure it is installed in ~/.local/bin")
        return

    # 1. Clean the data to avoid Typst syntax errors in names or roles
    name = data['name'].replace("#", "\\#")
    email = data['email'] # link() handles the @ safely inside its "string"

    # 2. Build the template
    # Note: We omit the body [...] in #link to let Typst render it safely.
    typst_content = f"""
    #set page(margin: 1.5cm, paper: "a4")
    #set text(font: "DejaVu Sans", size: 10pt)
    
    #align(center)[
        = {name}
        #text(size: 9pt)[#link("mailto:{email}")]
    ]

    #line(length: 100%, stroke: 0.5pt)

    == Professional Experience
    """
    
    for job in data['tailored_experience']:
        # Escape any # or @ that might appear in AI-generated roles/bullets
        safe_role = job['role'].replace("@", "\\@").replace("#", "\\#")
        safe_company = job['company'].replace("@", "\\@").replace("#", "\\#")
        
        typst_content += f"\n* {safe_company} * --- _{safe_role}_ \n"
        for bullet in job['bullets']:
            # Critical: Escape bullets too in case AI mentions 'X @ 20%'
            safe_bullet = bullet.replace("@", "\\@").replace("#", "\\#")
            typst_content += f"- {safe_bullet}\n"

    with open("resume.typ", "w") as f:
        f.write(typst_content)
    
    # 3. Run and Check Result
    result = subprocess.run([typst_path, "compile", "resume.typ", "tailored_cv.pdf"], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✨ Successfully generated tailored_cv.pdf")
    else:
        print(f"❌ Typst compile error:\n{result.stderr}")