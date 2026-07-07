import sqlite3
import os
from neuro_san.interfaces.coded_tool import CodedTool

class ResumeAnonymizerTool(CodedTool):
    async def async_invoke(self, args, sly_data):
        job_role = args.get("job_role", "")

        db_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "blindspot.db"
        )
        db_path = os.path.normpath(db_path)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM applicants WHERE job_role=?", (job_role,)
        ).fetchall()
        conn.close()

        if not rows:
            return {"error": f"No candidates found for: {job_role}"}

        anonymized = []
        for i, row in enumerate(rows):
            candidate_id = f"Candidate_{i+1:02d}"

            # Real identity sealed in sly_data — LLMs never see this
            sly_data[candidate_id] = {
                "name": row["name"],
                "resume_id": row["resume_id"]
            }

            # Only anonymized fields go to chat stream
            anonymized.append({
                "candidate_id": candidate_id,
                "skills": row["skills"],
                "experience_years": row["experience_years"],
                "education": row["education"],
                "certifications": row["certifications"],
                "projects_count": row["projects_count"]
            })

        print(f"[BLINDSPOT] {len(anonymized)} candidates anonymized "
              f"for '{job_role}'. Names sealed in sly_data.")

        return {"candidates": anonymized, "job_role": job_role}