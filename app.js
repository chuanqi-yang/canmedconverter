document.getElementById("add-course").addEventListener("click", () => {
  const container = document.getElementById("courses");
  const div = document.createElement("div");
  div.classList.add("course-row");

  div.innerHTML = `
    <input type="text" name="course" placeholder="Course Name" required>
    <input type="text" name="grade" placeholder="Grade (%) or Letter)" required>
    <input type="number" name="credits" placeholder="Credits" required>
    <button type="button" class="remove">x</button>
  `;

  div.querySelector(".remove").addEventListener("click", () => div.remove());
  container.appendChild(div);
});

document.getElementById("gpa-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const university = document.getElementById("university").value;
  const courseRows = document.querySelectorAll(".course-row");

  const courses = Array.from(courseRows).map(row => {
    return {
      course: row.querySelector('input[name="course"]').value,
      grade: row.querySelector('input[name="grade"]').value,
      credits: parseFloat(row.querySelector('input[name="credits"]').value)
    };
  });

  const response = await fetch("http://localhost:5000/calculate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({university, courses})
  });

  const result = await response.json();
  document.getElementById("results").textContent = JSON.stringify(result, null, 2);
});
