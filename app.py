from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

# Enable CORS manually if flask-cors isn't available
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# OUAC Conversion Scales (extracted from original HTML)
CONVERSION_SCALES = {
    "scale3": {
        "name": "Scale 3 (Percentage)",
        "conversions": {
            (90, 100): 4.00, (85, 89): 3.90, (80, 84): 3.70, (77, 79): 3.30,
            (73, 76): 3.00, (70, 72): 2.70, (67, 69): 2.30, (63, 66): 2.00,
            (60, 62): 1.70, (57, 59): 1.30, (53, 56): 1.00, (50, 52): 0.70,
            (0, 49): 0.00
        },
        "type": "percentage"
    },
    "scale6": {
        "name": "Scale 6 (Memorial University)",
        "conversions": {
            (94, 100): 4.00, (87, 93): 3.90, (80, 86): 3.70, (75, 79): 3.30,
            (70, 74): 3.00, (65, 69): 2.70, (60, 64): 2.30, (55, 59): 2.00,
            (50, 54): 1.70, (0, 49): 0.00
        },
        "type": "percentage"
    },
    "scale7": {
        "name": "Scale 7 (Letter Grades)",
        "conversions": {
            "A+": 4.00, "A": 3.90, "A-": 3.70, "B+": 3.30, "B": 3.00,
            "B-": 2.70, "C+": 2.30, "C": 2.00, "C-": 1.70, "D+": 1.30,
            "D": 1.00, "D-": 0.70, "F": 0.00, "E": 0.00
        },
        "type": "letter"
    },
    "scale8": {
        "name": "Scale 8 (McGill/Quest)",
        "conversions": {
            "A": 4.00, "A-": 3.70, "B+": 3.30, "B": 3.00, "B-": 2.70,
            "C+": 2.30, "C": 2.00, "C-": 1.70, "D+": 1.30, "D": 1.00,
            "F": 0.00
        },
        "type": "letter"
    },
    "scale9": {
        "name": "Scale 9 (Manitoba/York)",
        "conversions": {
            "A+": 4.00, "A": 3.90, "B+": 3.30, "B": 3.00, "C+": 2.30,
            "C": 2.00, "D+": 1.30, "D": 1.00, "F": 0.00
        },
        "type": "letter"
    }
}

# University to scale mapping
UNIVERSITY_SCALES = {
    "algoma": "scale3", "bishops": "scale3", "brock": "scale3", "cape_breton": "scale3",
    "guelph": "scale3", "lakehead": "scale3", "nipissing": "scale3", "ocad": "scale3",
    "pei": "scale3", "regina": "scale3", "saskatchewan": "scale3", "st_fx": "scale3",
    "trent": "scale3", "western": "scale3",
    
    "acadia": "scale7", "alberta": "scale7", "athabasca": "scale7", "brandon": "scale7",
    "calgary": "scale7", "carleton": "scale7", "capilano": "scale7", "concordia": "scale7",
    "laurentian": "scale7", "laval": "scale7", "lethbridge": "scale7", "mcmaster": "scale7",
    "moncton": "scale7", "montreal": "scale7", "mount_allison": "scale7", "mount_royal": "scale7",
    "mount_saint_vincent": "scale7", "unb": "scale7", "ontario_tech": "scale7", "ottawa": "scale7",
    "uqam": "scale7", "royal_roads": "scale7", "sherbrooke": "scale7", "sfu": "scale7",
    "saint_marys": "scale7", "st_thomas": "scale7", "sainte_anne": "scale7", "tru": "scale7",
    "tmu": "scale7", "trinity_western": "scale7", "ubc": "scale7", "unbc": "scale7",
    "laurier": "scale7", "winnipeg": "scale7",
    
    "memorial": "scale6",
    "mcgill": "scale8", "quest": "scale8",
    "manitoba": "scale9", "york": "scale9"
}

def convert_grade_to_gpa(grade, scale_type):
    """Convert a grade to GPA using the specified OUAC scale."""
    if not scale_type or scale_type not in CONVERSION_SCALES:
        return None
    
    scale = CONVERSION_SCALES[scale_type]
    grade_str = str(grade).strip().upper()
    
    if scale["type"] == "percentage":
        try:
            numeric_grade = float(grade_str)
            if numeric_grade < 0 or numeric_grade > 100:
                return None
                
            # Find the appropriate range
            for (min_val, max_val), gpa_val in scale["conversions"].items():
                if min_val <= numeric_grade <= max_val:
                    return gpa_val
        except ValueError:
            return None
    else:  # letter grades
        return scale["conversions"].get(grade_str)
    
    return None

def calculate_gpa_variations(courses_with_years):
    """Calculate various GPA types used by different medical schools."""
    results = {}
    
    # Group courses by academic year
    year_data = {}
    all_courses = []
    
    for course in courses_with_years:
        gpa = course["gpa"]
        credits = course["credits"]
        year = course.get("academic_year")
        
        if gpa is not None and credits > 0:
            course_data = {"gpa": gpa, "credits": credits, "year": year, "course": course["course"]}
            all_courses.append(course_data)
            
            if year:
                if year not in year_data:
                    year_data[year] = {"courses": [], "total_credits": 0, "weighted_sum": 0}
                year_data[year]["courses"].append(course_data)
                year_data[year]["total_credits"] += credits
                year_data[year]["weighted_sum"] += gpa * credits
    
    if not all_courses:
        return {"error": "No valid courses found"}
    
    # 1. Cumulative GPA (cGPA)
    total_credits = sum(course["credits"] for course in all_courses)
    total_weighted_sum = sum(course["gpa"] * course["credits"] for course in all_courses)
    results["cGPA"] = round(total_weighted_sum / total_credits, 3) if total_credits > 0 else 0
    results["total_courses"] = len(all_courses)
    results["total_credits"] = round(total_credits, 1)
    
    # 2. Year averages
    year_averages = []
    for year, data in year_data.items():
        if data["total_credits"] > 0:
            year_averages.append({
                "year": year,
                "gpa": round(data["weighted_sum"] / data["total_credits"], 3),
                "credits": round(data["total_credits"], 1),
                "courses": len(data["courses"])
            })
    
    year_averages.sort(key=lambda x: x["gpa"])  # Sort by GPA, lowest first
    results["year_breakdown"] = year_averages
    
    # 3. Adjusted GPA (Drop worst year)
    if len(year_averages) >= 2:
        full_years = [year for year in year_averages if year["credits"] >= 18]
        
        if len(full_years) >= 2:
            remaining_years = full_years[1:]  # Remove worst year
            adjusted_credits = sum(year["credits"] for year in remaining_years)
            adjusted_weighted_sum = sum(year["gpa"] * year["credits"] for year in remaining_years)
            
            results["adjusted_gpa"] = round(adjusted_weighted_sum / adjusted_credits, 3) if adjusted_credits > 0 else 0
            results["dropped_year"] = full_years[0]["year"]
        elif len(year_averages) >= 2:
            remaining_years = year_averages[1:]
            adjusted_credits = sum(year["credits"] for year in remaining_years)
            adjusted_weighted_sum = sum(year["gpa"] * year["credits"] for year in remaining_years)
            
            results["adjusted_gpa"] = round(adjusted_weighted_sum / adjusted_credits, 3) if adjusted_credits > 0 else 0
            results["dropped_year"] = year_averages[0]["year"]
            results["adjusted_note"] = "Note: Dropped year had fewer than 18 credits"
    
    # 4. Two Best Years GPA
    if len(year_averages) >= 2:
        best_two_years = sorted(year_averages, key=lambda x: x["gpa"], reverse=True)[:2]
        best_two_credits = sum(year["credits"] for year in best_two_years)
        best_two_weighted_sum = sum(year["gpa"] * year["credits"] for year in best_two_years)
        
        results["two_best_years_gpa"] = round(best_two_weighted_sum / best_two_credits, 3) if best_two_credits > 0 else 0
        results["best_two_years"] = [year["year"] for year in best_two_years]
    
    # 5. Three Most Recent Years
    if len(year_averages) >= 3:
        recent_three = sorted(year_averages, key=lambda x: x["year"], reverse=True)[:3]
        recent_three_credits = sum(year["credits"] for year in recent_three)
        recent_three_weighted_sum = sum(year["gpa"] * year["credits"] for year in recent_three)
        
        results["three_recent_years_gpa"] = round(recent_three_weighted_sum / recent_three_credits, 3) if recent_three_credits > 0 else 0
        results["recent_three_years"] = [year["year"] for year in recent_three]
    
    return results

@app.route("/universities", methods=["GET"])
def get_universities():
    """Return list of supported universities with their scales."""
    universities = []
    for uni_key, scale_key in UNIVERSITY_SCALES.items():
        scale_info = CONVERSION_SCALES[scale_key]
        universities.append({
            "key": uni_key,
            "name": uni_key.replace("_", " ").title(),
            "scale": scale_info["name"],
            "scale_key": scale_key
        })
    return jsonify(universities)

@app.route("/calculate", methods=["POST"])
def calculate_gpa():
    """Calculate GPA with enhanced medical school variations."""
    try:
        data = request.get_json()
        university = data.get("university", "").lower()
        courses = data.get("courses", [])
        
        if university not in UNIVERSITY_SCALES:
            return jsonify({"error": "University not supported"}), 400
        
        scale_type = UNIVERSITY_SCALES[university]
        processed_courses = []
        
        for course in courses:
            gpa = convert_grade_to_gpa(course["grade"], scale_type)
            processed_courses.append({
                "course": course.get("course", "Course"),
                "original_grade": course["grade"],
                "credits": float(course.get("credits", 1)),
                "academic_year": course.get("academic_year"),
                "gpa": gpa
            })
        
        # Calculate all GPA variations
        gpa_results = calculate_gpa_variations(processed_courses)
        
        if "error" in gpa_results:
            return jsonify(gpa_results), 400
        
        response = {
            "university": university,
            "scale_used": CONVERSION_SCALES[scale_type]["name"],
            "courses": processed_courses,
            **gpa_results
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/convert-grade", methods=["POST"])
def convert_single_grade():
    """Convert a single grade for real-time feedback."""
    try:
        data = request.get_json()
        grade = data.get("grade")
        university = data.get("university", "").lower()
        
        if university not in UNIVERSITY_SCALES:
            return jsonify({"error": "University not supported"}), 400
        
        scale_type = UNIVERSITY_SCALES[university]
        gpa = convert_grade_to_gpa(grade, scale_type)
        
        return jsonify({
            "original_grade": grade,
            "gpa": gpa,
            "scale": CONVERSION_SCALES[scale_type]["name"]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
