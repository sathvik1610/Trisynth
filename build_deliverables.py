import os
import shutil

# Ensure directory exists
out_dir = r"docs\deliverables"
os.makedirs(out_dir, exist_ok=True)

# 1. Technical Documentation = the project report followed by the backend implementation guide
tech_doc_path = os.path.join(out_dir, "Technical_Documentation.md")
with open("Project_Report.md", "r", encoding="utf-8") as f:
    report_content = f.read()

with open(r"docs\technical_documentation\implementation_guide_backend.md", "r", encoding="utf-8") as f:
    backend_content = f.read()

with open(tech_doc_path, "w", encoding="utf-8") as f:
    f.write(report_content)
    f.write("\n\n---\n\n")
    f.write(backend_content)

print("Created Technical_Documentation.md")

# 2. Language Manual (a copy of the canonical manual in the repository root)
lang_doc_path = os.path.join(out_dir, "Language_Manual.md")
shutil.copyfile("Language_Manual.md", lang_doc_path)
shutil.copyfile("Language_Manual.md", r"docs\technical_documentation\language_manual.md")
print("Created Language_Manual.md")

# 3. Installation Manual
inst_doc_path = os.path.join(out_dir, "Installation_Manual.md")
with open("INSTALL.md", "r", encoding="utf-8") as f:
    install_c = f.read()
with open("SETUP.md", "r", encoding="utf-8") as f:
    setup_c = f.read()

with open(inst_doc_path, "w", encoding="utf-8") as f:
    f.write(install_c)
    f.write("\n\n---\n\n")
    f.write(setup_c)

print("Created Installation_Manual.md")
