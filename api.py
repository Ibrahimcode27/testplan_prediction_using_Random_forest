from fastapi import FastAPI
import sqlite3

app = FastAPI()

# Database connection
def get_db_connection():
    conn = sqlite3.connect('exam_portal.db')
    conn.row_factory = sqlite3.Row
    return conn

# Endpoint to Fetch Test Plan
@app.post("/fetch_test_plan")
async def fetch_test_plan(subject: str):
    conn = get_db_connection()
    test_plan = conn.execute('SELECT * FROM test_plans WHERE subject = ?', (subject,)).fetchall()
    conn.close()
    return {"test_plan": [dict(row) for row in test_plan]}

# Endpoint to Fetch Questions
@app.post("/fetch_questions")
async def fetch_questions(subject: str):
    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM questions WHERE subject = ?', (subject,)).fetchall()
    conn.close()
    return {"questions": [dict(row) for row in questions]}
