import sqlite3
import csv

conn = sqlite3.connect('data/blindspot.db')

with open('data/resume_screening.csv', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

conn.execute('''CREATE TABLE IF NOT EXISTS applicants (
    resume_id TEXT, name TEXT, skills TEXT,
    experience_years REAL, education TEXT,
    certifications TEXT, job_role TEXT,
    recruiter_decision TEXT, salary_expectation REAL,
    projects_count INTEGER, ai_score REAL)''')

conn.executemany('INSERT INTO applicants VALUES (?,?,?,?,?,?,?,?,?,?,?)',
    [(r['Resume_ID'], r['Name'], r['Skills'],
      r['Experience (Years)'], r['Education'],
      r['Certifications'], r['Job Role'],
      r['Recruiter Decision'], r['Salary Expectation ($)'],
      r['Projects Count'], r['AI Score (0-100)']) for r in rows])

conn.commit()
conn.close()
print('Database created successfully')