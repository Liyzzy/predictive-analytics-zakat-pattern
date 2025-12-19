const API_BASE = "/api";

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("currentDate").textContent =
    new Date().toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });

  fetchDashboardData();
  setupPredictionForm();
});

async function fetchDashboardData() {
  try {
    const response = await fetch(`${API_BASE}/data`);
    const data = await response.json();

    // Update Stats
    document.getElementById("totalDonors").innerText = data.total_donors;
    document.getElementById("totalZakat").innerText = formatCurrency(
      data.total_zakat_pool
    );
    document.getElementById("avgZakat").innerText = formatCurrency(
      data.total_zakat_pool / data.total_donors
    );

    // Render Charts
    renderEmploymentChart(data.avg_zakat_by_employment);
    renderIncomeChart(data.income_vs_zakat);
  } catch (error) {
    console.error("Error fetching dashboard data:", error);
  }
}

function renderEmploymentChart(dataObj) {
  const ctx = document.getElementById("employmentChart").getContext("2d");

  const labels = Object.keys(dataObj).map((k) => {
    if (k == 0) return "Unemployed";
    if (k == 1) return "Employed";
    if (k == 2) return "Self-Employed";
    return k;
  });
  const values = Object.values(dataObj);

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Avg Zakat (RM)",
          data: values,
          backgroundColor: [
            "rgba(244, 63, 94, 0.7)",
            "rgba(6, 182, 212, 0.7)",
            "rgba(139, 92, 246, 0.7)",
          ],
          borderColor: [
            "rgba(244, 63, 94, 1)",
            "rgba(6, 182, 212, 1)",
            "rgba(139, 92, 246, 1)",
          ],
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: { beginAtZero: true, grid: { color: "rgba(255,255,255,0.1)" } },
        x: { grid: { display: false } },
      },
    },
  });
}

function renderIncomeChart(scatterData) {
  const ctx = document.getElementById("incomeChart").getContext("2d");

  const points = scatterData.map((d) => ({ x: d.Income, y: d.ZakatAmount }));

  new Chart(ctx, {
    type: "scatter",
    data: {
      datasets: [
        {
          label: "Income vs Zakat",
          data: points,
          backgroundColor: "rgba(6, 182, 212, 0.6)",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: "linear",
          position: "bottom",
          grid: { color: "rgba(255,255,255,0.1)" },
          title: { display: true, text: "Annual Income (RM)" },
        },
        y: {
          grid: { color: "rgba(255,255,255,0.1)" },
          title: { display: true, text: "Zakat Amount (RM)" },
        },
      },
    },
  });
}

function setupPredictionForm() {
  const form = document.getElementById("predictionForm");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      Age: Number(document.getElementById("p_age").value),
      Income: Number(document.getElementById("p_income").value),
      FamilySize: Number(document.getElementById("p_family").value),
      EmploymentStatus: Number(document.getElementById("p_employment").value),
      PreviousContributionScore: Number(
        document.getElementById("p_history").value
      ),
    };

    const btn = form.querySelector("button");
    const originalText = btn.innerText;
    btn.innerText = "Calculating...";
    btn.disabled = true;

    try {
      const response = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json();

      if (result.status === "success") {
        document.getElementById("resultAmount").innerText = formatCurrency(
          result.predicted_zakat
        );
        document
          .getElementById("predictionPlaceholder")
          .classList.add("hidden");
        document.getElementById("predictionResult").classList.remove("hidden");
      } else {
        alert("Prediction failed: " + result.error);
      }
    } catch (error) {
      console.error(error);
      alert("Error connecting to server.");
    } finally {
      btn.innerText = originalText;
      btn.disabled = false;
    }
  });
}

function formatCurrency(num) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "MYR",
  }).format(num);
}
