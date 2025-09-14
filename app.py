from flask import Flask, request, jsonify

app = Flask(__name__)

# --- GPA Conversion Logic ---
def convert_to_gpa(grade, university):
    """Convert percentage/letter grades to OMSAS 4.0 scale (simplified)."""
    try:
        grade = float(grade)
    except ValueError:
        # Handle letters (basic example, expand for more schools)
        letter_map = {"A+": 4.0, "A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7}
        return letter_map.get(grade.upper(), 0.0)

    if university == "UofT":
        if grade >= 85: return 4.0
        elif grade >= 80: return 3.7
        elif grade >= 75: return 3.3
        elif grade >= 70: return 3.0
        elif grade >= 65: return 2.7
        else: return 2.0

    if university == "UBC":
        if grade >= 90: return 4.0
        elif grade >= 85: return 3.9
        elif grade >= 80: return 3.7
        elif grade >= 75: return 3.3
        else: return 2.0

    # default
    return 0.0


@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.get_json()
    university = data["university"]
    courses = data["courses"]

    total_points = 0
    total_credits = 0
    course_results = []

    for c in courses:
        gpa = convert_to_gpa(c["grade"], university)
        weighted = gpa * c["credits"]
        total_points += weighted
        total_credits += c["credits"]

        course_results.append({
            "course": c["course"],
            "grade": c["grade"],
            "credits": c["credits"],
            "gpa": gpa
        })

    overall_gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0

    return jsonify({
        "university": university,
        "overall_gpa": overall_gpa,
        "courses": course_results
    })


if __name__ == "__main__":
    app.run(debug=True)
