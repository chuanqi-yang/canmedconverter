// Configuration
const API_BASE_URL = "http://localhost:5001";

// Global state
let universities = [];
let currentScale = null;

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    await loadUniversities();
    addCourseRow(); // Add initial row
    setupEventListeners();
});

// Load universities from API
async function loadUniversities() {
    console.log('Loading universities...');
    try {
        const response = await fetch(`${API_BASE_URL}/universities`);
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        universities = await response.json();
        console.log('Universities loaded:', universities.length);
        
        const universitySelect = document.getElementById('university');
        universities.forEach(uni => {
            const option = document.createElement('option');
            option.value = uni.key;
            option.textContent = `${uni.name} (${uni.scale})`;
            universitySelect.appendChild(option);
        });
        console.log('University options added to select');
    } catch (error) {
        console.error('Error loading universities:', error);
        showError('Failed to load universities. Please check if the server is running on http://localhost:5000');
    }
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('university').addEventListener('change', handleUniversityChange);
    document.getElementById('add-course').addEventListener('click', addCourseRow);
    document.getElementById('gpa-form').addEventListener('submit', calculateGPA);
    document.getElementById('clear-all').addEventListener('click', clearAll);
}

// Handle university selection
function handleUniversityChange(event) {
    const universityKey = event.target.value;
    const scaleInfo = document.getElementById('scale-info');
    
    if (universityKey) {
        const university = universities.find(u => u.key === universityKey);
        currentScale = university;
        
        scaleInfo.innerHTML = `<strong>Selected Scale:</strong> ${university.scale}`;
        scaleInfo.style.display = 'block';
        
        // Update existing grade inputs
        updateAllGradeConversions();
    } else {
        scaleInfo.style.display = 'none';
        currentScale = null;
    }
    
    clearResults();
}

// Add a new course row
function addCourseRow() {
    const tbody = document.getElementById('courses');
    const row = document.createElement('tr');
    row.className = 'course-row';
    
    // Generate academic year options
    let yearOptions = '<option value="">Select Academic Year</option>';
    for (let year = 2010; year <= 2030; year++) {
        yearOptions += `<option value="${year}-${year+1}">Academic Year ${year}-${year+1}</option>`;
    }
    
    const placeholder = currentScale ? getGradePlaceholder(currentScale.scale) : 'Enter grade';
    
    row.innerHTML = `
        <td><input type="text" name="course" placeholder="Course Name" class="course-input"></td>
        <td><input type="text" name="grade" placeholder="${placeholder}" class="grade-input" required></td>
        <td><input type="number" name="credits" placeholder="3.0" step="0.1" min="0" class="credit-input" required></td>
        <td><select name="academic-year" class="year-select">${yearOptions}</select></td>
        <td class="gpa-display">-</td>
        <td><button type="button" class="remove-btn" onclick="removeRow(this)">Remove</button></td>
    `;
    
    // Add real-time grade conversion
    const gradeInput = row.querySelector('.grade-input');
    gradeInput.addEventListener('input', () => convertGradeRealTime(gradeInput));
    
    tbody.appendChild(row);
}

// Remove a course row
function removeRow(button) {
    button.closest('tr').remove();
}

// Get appropriate placeholder text for grade input
function getGradePlaceholder(scaleName) {
    if (scaleName.includes('Percentage')) {
        return 'Enter percentage (0-100)';
    } else {
        return 'Enter letter grade (A+, A, B+, etc.)';
    }
}

// Real-time grade conversion
async function convertGradeRealTime(gradeInput) {
    if (!currentScale || !gradeInput.value.trim()) {
        gradeInput.closest('tr').querySelector('.gpa-display').textContent = '-';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/convert-grade`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                grade: gradeInput.value.trim(),
                university: currentScale.key
            })
        });
        
        const result = await response.json();
        const gpaDisplay = gradeInput.closest('tr').querySelector('.gpa-display');
        
        if (result.gpa !== null && result.gpa !== undefined) {
            gpaDisplay.textContent = result.gpa.toFixed(2);
            gpaDisplay.style.color = '#27ae60';
        } else {
            gpaDisplay.textContent = 'Invalid';
            gpaDisplay.style.color = '#e74c3c';
        }
    } catch (error) {
        gradeInput.closest('tr').querySelector('.gpa-display').textContent = 'Error';
    }
}

// Update all grade conversions when university changes
function updateAllGradeConversions() {
    const gradeInputs = document.querySelectorAll('.grade-input');
    gradeInputs.forEach(input => {
        if (input.value.trim()) {
            convertGradeRealTime(input);
        }
        input.placeholder = getGradePlaceholder(currentScale.scale);
    });
}

// Calculate GPA
async function calculateGPA(event) {
    event.preventDefault();
    
    if (!currentScale) {
        showError('Please select a university first.');
        return;
    }
    
    const courseRows = document.querySelectorAll('.course-row');
    if (courseRows.length === 0) {
        showError('Please add at least one course.');
        return;
    }
    
    // Collect course data
    const courses = Array.from(courseRows).map(row => {
        const course = row.querySelector('[name="course"]').value || 'Course';
        const grade = row.querySelector('[name="grade"]').value.trim();
        const credits = parseFloat(row.querySelector('[name="credits"]').value) || 0;
        const academicYear = row.querySelector('[name="academic-year"]').value;
        
        return { course, grade, credits, academic_year: academicYear };
    });
    
    // Validate courses
    const validCourses = courses.filter(c => c.grade && c.credits > 0);
    if (validCourses.length === 0) {
        showError('Please enter valid grades and credits for at least one course.');
        return;
    }
    
    showLoading(true);
    clearError();
    
    try {
        const response = await fetch(`${API_BASE_URL}/calculate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                university: currentScale.key,
                courses: validCourses
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Calculation failed');
        }
        
        const results = await response.json();
        displayResults(results);
        
    } catch (error) {
        showError(`Calculation failed: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// Display comprehensive results
function displayResults(results) {
    const resultsSection = document.getElementById('results-section');
    const resultsDiv = document.getElementById('results');
    
    let html = `
        <div class="result-header">
            <h3>University: ${results.university.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h3>
            <p>Scale Used: ${results.scale_used}</p>
        </div>
    `;
    
    // Cumulative GPA
    html += `
        <div class="gpa-result primary">
            <h4>Cumulative GPA (cGPA)</h4>
            <div class="gpa-value">${results.cGPA}</div>
            <p class="gpa-details">Based on ${results.total_courses} courses (${results.total_credits} total credits)</p>
        </div>
    `;
    
    // Year breakdown
    if (results.year_breakdown && results.year_breakdown.length > 0) {
        html += '<div class="gpa-result"><h4>Year-by-Year Breakdown</h4><ul>';
        results.year_breakdown
            .sort((a, b) => b.year.localeCompare(a.year))
            .forEach(year => {
                html += `<li><strong>${year.year}:</strong> ${year.gpa} GPA (${year.credits} credits, ${year.courses} courses)</li>`;
            });
        html += '</ul></div>';
    }
    
    // Adjusted GPA (Drop worst year)
    if (results.adjusted_gpa !== undefined) {
        html += `
            <div class="gpa-result weighted">
                <h4>Adjusted GPA (Worst Year Dropped)</h4>
                <div class="gpa-value">${results.adjusted_gpa}</div>
                <p class="gpa-details">
                    Dropped: ${results.dropped_year}
                    ${results.adjusted_note ? `<br><em>${results.adjusted_note}</em>` : ''}
                    <br><strong>Used by:</strong> University of Calgary, University of Alberta, UBC
                </p>
            </div>
        `;
    }
    
    // Two Best Years GPA
    if (results.two_best_years_gpa !== undefined) {
        html += `
            <div class="gpa-result weighted">
                <h4>Two Best Years GPA</h4>
                <div class="gpa-value">${results.two_best_years_gpa}</div>
                <p class="gpa-details">
                    Years used: ${results.best_two_years.join(', ')}
                    <br><strong>Used by:</strong> Western University, Dalhousie University
                </p>
            </div>
        `;
    }
    
    // Three Most Recent Years GPA
    if (results.three_recent_years_gpa !== undefined) {
        html += `
            <div class="gpa-result weighted">
                <h4>Three Most Recent Years GPA</h4>
                <div class="gpa-value">${results.three_recent_years_gpa}</div>
                <p class="gpa-details">
                    Years used: ${results.recent_three_years.join(', ')}
                    <br><strong>Used by:</strong> University of Ottawa
                </p>
            </div>
        `;
    }
    
    // Important notes
    html += `
        <div class="gpa-result info">
            <h4>Important Notes</h4>
            <ul>
                <li>Different medical schools use different calculation methods</li>
                <li>Some schools require minimum 18 credits per year for "worst year" dropping</li>
                <li>Always verify GPA calculations with official school requirements</li>
                <li>Graduate coursework may be treated differently by some schools</li>
            </ul>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Utility functions
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => errorDiv.style.display = 'none', 8000);
}

function clearError() {
    document.getElementById('error').style.display = 'none';
}

function clearResults() {
    document.getElementById('results-section').style.display = 'none';
}

function clearAll() {
    // Clear all course rows
    document.getElementById('courses').innerHTML = '';
    
    // Reset university selection
    document.getElementById('university').value = '';
    document.getElementById('scale-info').style.display = 'none';
    currentScale = null;
    
    // Clear results and errors
    clearResults();
    clearError();
    
    // Add initial row
    addCourseRow();
}
