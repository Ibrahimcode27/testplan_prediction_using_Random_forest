from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import joblib
import numpy as np

# Initialize the FastAPI app
app = FastAPI()

# Load the Random Forest model
rf_model = joblib.load("random_forest_model.pkl")

# Load the syllabus data
with open("cleaned.json", "r") as f:
    syllabus = json.load(f)

# Define request models
class PlanRequest(BaseModel):
    target_marks: int
    weak_subject: str
    strong_subject: str
    available_time: int  # Available time in days

class FeedbackData(BaseModel):
    weightage: int
    accuracy: int
    time_spent: int
    num_tests: int
    chapter_difficulty: int

# Rule-based algorithm for initial test plan generation
def generate_test_plan(target_marks, weak_subject, strong_subject, available_time):
    allocated_marks = {}
    
    # Rule-based allocation of marks
    if strong_subject == "Chemistry":
        allocated_marks["Chemistry"] = 180
        remaining_marks = target_marks - 180
        if weak_subject == "Biology":
            allocated_marks["Physics"] = min(remaining_marks * 0.55, 180)
            allocated_marks["Biology"] = target_marks - allocated_marks["Chemistry"] - allocated_marks["Physics"]
        elif weak_subject == "Physics":
            allocated_marks["Biology"] = min(remaining_marks * 0.55, 360)
            allocated_marks["Physics"] = target_marks - allocated_marks["Chemistry"] - allocated_marks["Biology"]
    elif strong_subject == "Biology":
        allocated_marks["Biology"] = 360
        remaining_marks = target_marks - 360
        if remaining_marks < 0:
            allocated_marks["Biology"] = target_marks * 0.5
            allocated_marks["Chemistry"] = target_marks * 0.25
            allocated_marks["Physics"] = target_marks * 0.25
        elif weak_subject == "Physics":
            allocated_marks["Chemistry"] = min(remaining_marks * 0.55, 180)
            allocated_marks["Physics"] = target_marks - allocated_marks["Biology"] - allocated_marks["Chemistry"]
        elif weak_subject == "Chemistry":
            allocated_marks["Physics"] = min(remaining_marks * 0.55, 180)
            allocated_marks["Chemistry"] = target_marks - allocated_marks["Biology"] - allocated_marks["Physics"]
    elif strong_subject == "Physics":
        allocated_marks["Physics"] = 180
        remaining_marks = target_marks - 180
        if weak_subject == "Chemistry":
            allocated_marks["Biology"] = min(remaining_marks * 0.55, 360)
            allocated_marks["Chemistry"] = target_marks - allocated_marks["Physics"] - allocated_marks["Biology"]
        elif weak_subject == "Biology":
            allocated_marks["Chemistry"] = min(remaining_marks * 0.55, 180)
            allocated_marks["Biology"] = target_marks - allocated_marks["Physics"] - allocated_marks["Chemistry"]

    # Generate the test plan
    subject_wise_plan = {}
    chapter_wise_plan = []
    for subject, marks in allocated_marks.items():
        if subject not in syllabus:
            continue

        chapters = syllabus[subject]
        total_weightage = sum(int(chapters[ch]["weightage"]) for ch in chapters)
        subject_plan = []
        total_time = available_time * (marks / target_marks)

        for chapter, details in chapters.items():
            chapter_weightage = int(details.get("weightage", 0))
            allocated_marks_chapter = max(1, int((chapter_weightage / total_weightage) * marks))
            allocated_questions = allocated_marks_chapter // 4
            allocated_time = total_time * (allocated_marks_chapter / marks)

            # Prepare the response for the chapter
            chapter_plan = {
                "chapter": chapter,
                "allocated_questions": allocated_questions,
                "allocated_time": f"{allocated_time:.2f} days",
                "recommended_tests": max(1, allocated_questions // 3),
            }
            subject_plan.append(chapter_plan)
            chapter_wise_plan.append(chapter_plan)

        subject_wise_plan[subject] = {"chapters": subject_plan}
    
    return subject_wise_plan, chapter_wise_plan

# Route for generating the test plan using rule-based logic
@app.post("/generate_test_plan")
def generate_plan(plan: PlanRequest):
    subject_wise_plan, chapter_wise_plan = generate_test_plan(
        plan.target_marks, plan.weak_subject, plan.strong_subject, plan.available_time
    )
    return {"subject_wise_plan": subject_wise_plan, "chapter_wise_plan": chapter_wise_plan}

@app.post("/personalize_test_plan")
def personalize_plan(feedback: FeedbackData):
    # Prepare input for the model with 5 features
    model_input = np.array([[feedback.weightage, feedback.accuracy, feedback.time_spent, feedback.num_tests, feedback.chapter_difficulty]])
    
    # Predict recommended tests using the model
    recommended_tests = rf_model.predict(model_input)[0]
    
    # Apply custom rules to modify the prediction
    if feedback.accuracy > 75:
        if feedback.num_tests > 2:
            recommended_tests = 0
        elif feedback.num_tests > 1:
            recommended_tests = 1
    elif feedback.accuracy < 30:
        pass  # Keep the predicted value as is if accuracy < 30%
    
    # Build the updated test plan using the modified recommended_tests
    updated_plan = {
        "allocated_questions": max(1, int(recommended_tests) * 3),
        "allocated_time": f"{max(1, recommended_tests * 1.5):.2f} days",
        "recommended_tests": int(recommended_tests)
    }
    return updated_plan
