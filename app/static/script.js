// -------------------------
// STUDENT DASHBOARD CHART
// -------------------------

function renderMarksChart(marksData) {
    const labels = marksData.map(m => m.subject);
    const marks = marksData.map(m => m.marks);

    new Chart(document.getElementById("marksChart"), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: "Marks",
                data: marks,
                backgroundColor: "rgba(54, 162, 235, 0.6)"
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: { y: { beginAtZero: true, max: 100 } }
        }
    });
}

// -------------------------
// FACULTY DASHBOARD: ADD MARKS
// -------------------------

function addMarks(student_id, btn) {
    const row = btn.parentElement.parentElement;
    const subject = row.querySelector('[name="subject"]').value;
    const marks = row.querySelector('[name="marks"]').value;

    fetch('/faculty/add-marks', {
        method: 'POST',
        body: new URLSearchParams({ student_id, subject, marks })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.msg);
        // Optionally clear inputs
        row.querySelector('[name="subject"]').value = "";
        row.querySelector('[name="marks"]').value = "";
    })
    .catch(err => alert("Error: " + err));
}

// -------------------------
// THEME TOGGLE
// -------------------------

function toggleTheme() {
    document.body.classList.toggle("dark");
}