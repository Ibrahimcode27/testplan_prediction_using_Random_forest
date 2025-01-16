from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime
from prediction import generate_test_plan, personalize_test_plan

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_test_plan', methods=['POST'])
def generate_plan():
    try:
        # Get form data
        exam_year = int(request.form['exam_year'])
        target_marks = int(request.form['target_marks'])
        weak_subject = request.form['weak_subject']
        strong_subject = request.form['strong_subject']

        # Calculate available time
        exam_date = datetime(exam_year, 5, 4)
        today = datetime.now()
        available_time = (exam_date - today).days
        if available_time <= 0:
            raise ValueError("Exam date is in the past or invalid.")

        # Generate the initial test plan using rule-based algorithm
        subject_wise_plan, chapter_wise_plan = generate_test_plan(
            target_marks, weak_subject, strong_subject, available_time
        )

        # Render the initial test plan
        return render_template(
            'test_plan.html',
            subject_wise_plan=subject_wise_plan,
            chapter_wise_plan=chapter_wise_plan,
            feedback_mode=False
        )
    except Exception as e:
        return render_template('error.html', message=f"An error occurred: {str(e)}"), 500

@app.route('/update_plan', methods=['POST'])
def update_plan():
    try:
        # Get form data
        feedback_data = request.form.to_dict()

        # Generate updated plan
        updated_plan = personalize_test_plan(feedback_data)

        # Render the updated plan
        return render_template('updated_plan.html', updated_plan=updated_plan)
    except Exception as e:
        return render_template('error.html', message=f"An error occurred: {str(e)}"), 500

if __name__ == '__main__':
    app.run(debug=True)
