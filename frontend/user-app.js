const API_BASE = "/api";

document.addEventListener("DOMContentLoaded", () => {
  // Set current date
  document.getElementById("currentDate").textContent =
    new Date().toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });

  // Fetch Nisab threshold
  fetchNisabThreshold();

  loadUserProfile();
  setupProfileForm();
  setupHaulTracker();
  loadContributionHistory();
  setupRealTimeWealth();
  setupLogout();
  setupScrollSpy();
});

// Load persistent user profile
async function loadUserProfile() {
  try {
    const response = await fetch(`${API_BASE}/user/profile`);
    
    if (response.status === 401) {
       return; // Not logged in
    }
    
    if (response.status === 404) {
       console.log("No existing profile found. User needs to create one.");
       return; 
    }

    const data = await response.json();

    if (data.status === "success" && data.profile) {
       const p = data.profile;
       
       // Populate form fields
       if(p.income) document.getElementById("income").value = (p.income / 12).toFixed(0); 
       if(p.age) document.getElementById("age").value = p.age;
       if(p.savings) document.getElementById("savings").value = p.savings;
       if(p.gold_value) document.getElementById("goldValue").value = p.gold_value;
       if(p.investment_value) document.getElementById("investmentValue").value = p.investment_value;
       if(p.family_size) document.getElementById("familySize").value = p.family_size;
       if(p.employment_status) document.getElementById("employmentStatus").value = p.employment_status;
       


       // Trigger wealth summary update
       updateWealthSummary();
       
       console.log("User profile loaded successfully");
       showToast("Welcome back! Your profile has been loaded.", "success");
    }
  } catch (error) {
    console.error("Error loading user profile:", error);
  }
}

// Logout function
function setupLogout() {
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        await fetch(`${API_BASE}/auth/logout`, {
          method: "POST",
          credentials: "include",
        });
      } catch (error) {
        console.error("Logout error:", error);
      }
      // Redirect to home regardless of API response
      window.location.href = "/";
    });
  }
}

async function fetchNisabThreshold() {
  try {
    const response = await fetch(`${API_BASE}/nisab`);
    const data = await response.json();
    document.getElementById("nisabValue").textContent = formatCurrency(
      data.nisab_threshold
    );
  } catch (error) {
    console.error("Error fetching Nisab:", error);
  }
}

function setupRealTimeWealth() {
  const inputs = ["savings", "goldValue", "investmentValue"];
  inputs.forEach((id) => {
    document.getElementById(id).addEventListener("input", updateWealthSummary);
  });
}

function updateWealthSummary() {
  const savings = Number(document.getElementById("savings").value) || 0;
  const gold = Number(document.getElementById("goldValue").value) || 0;
  const investments =
    Number(document.getElementById("investmentValue").value) || 0;
  const total = savings + gold + investments;

  document.getElementById("breakdownSavings").textContent =
    formatCurrency(savings);
  document.getElementById("breakdownGold").textContent = formatCurrency(gold);
  document.getElementById("breakdownInvestments").textContent =
    formatCurrency(investments);
  document.getElementById("totalWealth").textContent = formatCurrency(total);

  // Update wealth summary visibility
  const wealthSummary = document.getElementById("wealthSummary");
  wealthSummary.classList.add("visible");
}

function setupProfileForm() {
  const form = document.getElementById("profileForm");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      income: Number(document.getElementById("income").value) * 12, // Convert monthly to annual
      age: Number(document.getElementById("age").value),
      savings: Number(document.getElementById("savings").value),
      goldValue: Number(document.getElementById("goldValue").value),
      investmentValue: Number(document.getElementById("investmentValue").value),
      familySize: Number(document.getElementById("familySize").value),
      employmentStatus: Number(
        document.getElementById("employmentStatus").value
      ),
      previousContributionScore: 50, // Default value as UI input removed
    };

    const btn = form.querySelector("button");
    const originalText = btn.innerText;
    btn.innerText = "Calculating...";
    btn.disabled = true;

    try {
      // First check Nisab eligibility
      const nisabResponse = await fetch(`${API_BASE}/user/nisab-check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const nisabResult = await nisabResponse.json();

      updateNisabBanner(nisabResult);

      // Then get prediction
      const predResponse = await fetch(`${API_BASE}/user/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const predResult = await predResponse.json();

      if (predResult.status === "success") {
        displayPrediction(predResult);
        showToast("Profile saved & prediction updated successfully!", "success");
      } else {
        console.error("Prediction failed:", predResult.error);
        showToast("Failed to calculate prediction.", "error");
      }
    } catch (error) {
      console.error("Error:", error);
      showToast("Error connecting to server.", "error");
    } finally {
      btn.innerText = originalText;
      btn.disabled = false;
    }
  });
}

function updateNisabBanner(result) {
  const banner = document.getElementById("nisabBanner");
  const statusDiv = document.getElementById("nisabStatus");

  if (result.is_eligible) {
    banner.classList.add("eligible");
    banner.classList.remove("not-eligible");
    statusDiv.innerHTML = `
            <span class="status-icon"><i class="ph ph-check-circle"></i></span>
            <span class="status-text">Zakat is <strong>obligatory</strong> - Your wealth (${formatCurrency(
              result.total_wealth
            )}) exceeds the Nisab threshold</span>
        `;
  } else {
    banner.classList.add("not-eligible");
    banner.classList.remove("eligible");
    statusDiv.innerHTML = `
            <span class="status-icon"><i class="ph ph-info"></i></span>
            <span class="status-text">Zakat is <strong>not obligatory</strong> - Your wealth (${formatCurrency(
              result.total_wealth
            )}) is below the Nisab threshold</span>
        `;
  }
}

function displayPrediction(result) {
  document.getElementById("predictionPlaceholder").classList.add("hidden");
  document.getElementById("predictionResult").classList.remove("hidden");

  document.getElementById("predictedAmount").textContent = formatCurrency(
    result.predicted_zakat
  );
  document.getElementById("standardAmount").textContent = formatCurrency(
    result.standard_zakat
  );

  // Add animation
  document.getElementById("predictionResult").style.animation =
    "fadeIn 0.5s ease";
}

function setupHaulTracker() {
  const checkBtn = document.getElementById("checkHaulBtn");

  checkBtn.addEventListener("click", async () => {
    const haulStartDate = document.getElementById("haulStartDate").value;

    if (!haulStartDate) {
      alert("Please select the date when your wealth first reached Nisab.");
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/user/haul-status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ haulStartDate }),
      });
      const result = await response.json();

      displayHaulStatus(result);
    } catch (error) {
      console.error("Error:", error);
      alert("Error checking Haul status.");
    }
  });
}

function displayHaulStatus(result) {
  const haulResult = document.getElementById("haulResult");
  haulResult.classList.remove("hidden");

  if (result.is_due) {
    // Zakat is due
    document.getElementById("haulPercent").textContent = "100%";
    document.getElementById("daysElapsed").textContent = result.days_completed;
    document.getElementById("daysRemaining").textContent = "0";
    document.getElementById("dueDate").textContent = "NOW";
    document.getElementById("haulMessage").innerHTML = `
            <div class="haul-due">
                <span class="due-icon"><i class="ph ph-warning"></i></span>
                ${result.message}
            </div>
        `;

    // Set progress circle to full
    setProgressCircle(100);
  } else {
    document.getElementById(
      "haulPercent"
    ).textContent = `${result.progress_percent}%`;
    document.getElementById("daysElapsed").textContent = result.days_completed;
    document.getElementById("daysRemaining").textContent =
      result.days_remaining;
    document.getElementById("dueDate").textContent = formatDate(
      result.due_date
    );
    document.getElementById("haulMessage").innerHTML = `
            <div class="haul-pending">
                <span class="pending-icon"><i class="ph ph-calendar"></i></span>
                Your Zakat will be due on ${formatDate(result.due_date)}
            </div>
        `;

    setProgressCircle(result.progress_percent);
  }
}

function setProgressCircle(percent) {
  const circle = document.getElementById("haulProgressCircle");
  const circumference = 2 * Math.PI * 45; // r = 45
  const offset = circumference - (percent / 100) * circumference;
  circle.style.strokeDasharray = circumference;
  circle.style.strokeDashoffset = offset;
}

async function loadContributionHistory() {
  try {
    // Using mock donor ID for demo
    const response = await fetch(`${API_BASE}/user/history/MZ1001`);
    const result = await response.json();

    if (result.history) {
      renderHistoryChart(result.history);
      updateHistoryStats(result);
    }
  } catch (error) {
    console.error("Error loading history:", error);
    // Use fallback data
    const fallbackHistory = [
      { year: 2021, amount: 1200 },
      { year: 2022, amount: 1450 },
      { year: 2023, amount: 1680 },
      { year: 2024, amount: 1820 },
    ];
    renderHistoryChart(fallbackHistory);
  }
}

function renderHistoryChart(historyData) {
  const ctx = document.getElementById("historyChart").getContext("2d");

  const years = historyData.map((h) => h.year);
  const amounts = historyData.map((h) => h.amount);

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: years,
      datasets: [
        {
          label: "Zakat Contribution (RM)",
          data: amounts,
          backgroundColor: "rgba(5, 150, 105, 0.6)",
          borderColor: "rgba(5, 150, 105, 1)",
          borderWidth: 2,
          borderRadius: 8,
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
        y: {
          beginAtZero: true,
          grid: { color: "rgba(255,255,255,0.1)" },
          ticks: { color: "#94a3b8" },
        },
        x: {
          grid: { display: false },
          ticks: { color: "#94a3b8" },
        },
      },
    },
  });
}

function updateHistoryStats(result) {
  document.getElementById("totalContributed").textContent = formatCurrency(
    result.total_contributed
  );
  document.getElementById("yearsActive").textContent = result.history.length;

  // Calculate growth rate
  const history = result.history;
  if (history.length >= 2) {
    const lastYear = history[history.length - 1].amount;
    const prevYear = history[history.length - 2].amount;
    const growth = ((lastYear - prevYear) / prevYear) * 100;
    document.getElementById("growthRate").textContent = `${
      growth > 0 ? "+" : ""
    }${growth.toFixed(1)}%`;
  }
}

function formatCurrency(num) {
  return new Intl.NumberFormat("en-MY", {
    style: "currency",
    currency: "MYR",
  }).format(num);
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString("en-MY", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  
  const icon = type === "success" ? '<i class="ph ph-check-circle"></i>' : '<i class="ph ph-x-circle"></i>';
  
  toast.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <span class="toast-message">${message}</span>
  `;

  container.appendChild(toast);

  // Remove after animation (3 seconds total)
  setTimeout(() => {
    toast.remove();
  }, 3000);
}

function setupScrollSpy() {
  const sections = document.querySelectorAll("section[id]");
  const navLinks = document.querySelectorAll(".nav-links li a");
  
  window.addEventListener("scroll", () => {
    let current = "";
    sections.forEach((section) => {
      const sectionTop = section.offsetTop;
      const sectionHeight = section.clientHeight;
      if (pageYOffset >= sectionTop - 150) {
        current = section.getAttribute("id");
      }
    });

    navLinks.forEach((a) => {
      a.parentElement.classList.remove("active");
      if (a.getAttribute("href").includes(current) && current !== "") {
        a.parentElement.classList.add("active");
      }
    });
  });
}
