import json
import joblib
import numpy as np

# Load the JSON file
with open("cleaned.json", "r") as f:
    syllabus = json.load(f)

def generate_test_plan(target_marks, weak_subject, strong_subject, available_time):
    # Allocate initial marks based on strong subject
    allocated_marks = {}
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

    print(f"Allocated marks: {allocated_marks}")

    # Generate the test plan
    subject_wise_plan = {}
    chapter_wise_plan = []

    for subject, marks in allocated_marks.items():
        if subject not in syllabus:
            print(f"Skipping subject '{subject}' as it is not in the syllabus.")
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

            chapter_plan = {
                "chapter": chapter,
                "allocated_questions": allocated_questions,
                "allocated_time": f"{allocated_time:.2f} days",
                "recommended_tests": max(1, allocated_questions // 3),
            }
            subject_plan.append(chapter_plan)
            chapter_wise_plan.append(chapter_plan)

        subject_wise_plan[subject] = {"chapters": subject_plan}

    print("\nSubject-Wise Plan:")
    print(json.dumps(subject_wise_plan, indent=4))
    print("\nChapter-Wise Plan:")
    print(json.dumps(chapter_wise_plan, indent=4))

    return subject_wise_plan, chapter_wise_plan



# Load the saved Random Forest model
rf_model = joblib.load("random_forest_model.pkl")

def personalize_test_plan(feedback_data):
    # Extract necessary fields from the feedback
    weightage = int(feedback_data.get("weightage", 0))
    accuracy = int(feedback_data.get("accuracy", 75))  # Default accuracy
    time_spent = int(feedback_data.get("time_spent", 4))  # Default hours
    num_tests = int(feedback_data.get("num_tests", 2))  # Default number of tests
    chapter_difficulty = int(feedback_data.get("chapter_difficulty", 2))  # Default difficulty
    difficulty = feedback_data.get("difficulty", "Medium")  # Default difficulty

    # Convert difficulty to a numeric representation for the model
    difficulty_mapping = {"Low": 1, "Medium": 2, "High": 3}
    difficulty_numeric = difficulty_mapping.get(difficulty, 2)  # Default to Medium if not found

    # Prepare input for the model
    model_input = np.array([[weightage, accuracy, time_spent, num_tests, chapter_difficulty, difficulty_numeric]])
    recommended_tests = rf_model.predict(model_input)[0]

    # Build the updated test plan
    updated_plan = {
        "allocated_questions": recommended_tests * 3,  # Example logic
        "allocated_time": f"{recommended_tests * 1.5:.2f} days",  # Example logic
        "recommended_tests": recommended_tests
    }
    return updated_plan
