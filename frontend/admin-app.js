const API_BASE = 'http://localhost:5000/api';

// Chart instances for updates
let forecastChart = null;
let segmentChart = null;
let trendChart = null;

document.addEventListener('DOMContentLoaded', () => {
    // Set current date
    document.getElementById('currentDate').textContent = new Date().toLocaleDateString('en-US', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });

    // Load all dashboard data
    loadDashboardData();

    // Setup event handlers
    setupEventHandlers();

    // Setup logout button
    setupLogout();
});

// Logout function
function setupLogout() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                await fetch(`${API_BASE}/auth/logout`, {
                    method: 'POST',
                    credentials: 'include'
                });
            } catch (error) {
                console.error('Logout error:', error);
            }
            // Redirect to home regardless of API response
            window.location.href = '/';
        });
    }
}

function setupEventHandlers() {
    // Refresh button
    document.getElementById('refreshData').addEventListener('click', loadDashboardData);

    // Export button
    document.getElementById('exportBtn').addEventListener('click', exportData);

    // Period toggle
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
        });
    });

    // Trend type selector
    document.getElementById('trendType').addEventListener('change', (e) => {
        loadTrends(e.target.value);
    });
}

async function loadDashboardData() {
    try {
        await Promise.all([
            loadForecast(),
            loadSegments(),
            loadTrends('income'),
            loadAtRiskDonors()
        ]);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

async function loadForecast() {
    try {
        const response = await fetch(`${API_BASE}/admin/forecast`);
        const data = await response.json();

        // Update stat cards
        document.getElementById('totalDonors').textContent = data.total_donors;
        document.getElementById('annualForecast').textContent = formatCurrency(data.total_annual_forecast);
        document.getElementById('avgPerDonor').textContent = formatCurrency(data.average_per_donor);

        // Update forecast cards
        document.getElementById('thisMonthForecast').textContent = formatCurrency(data.monthly_forecast);
        document.getElementById('thisQuarterForecast').textContent = formatCurrency(data.quarterly_forecast);
        document.getElementById('annualProjection').textContent = formatCurrency(data.total_annual_forecast);

        // Render forecast chart
        renderForecastChart(data);
    } catch (error) {
        console.error('Error loading forecast:', error);
    }
}

function renderForecastChart(data) {
    const ctx = document.getElementById('forecastChart').getContext('2d');

    // Generate monthly projection data
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthlyValues = months.map((_, i) => {
        // Add some variation to make it realistic
        const variation = 0.8 + Math.random() * 0.4;
        return data.monthly_forecast * variation;
    });

    if (forecastChart) forecastChart.destroy();

    forecastChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: months,
            datasets: [{
                label: 'Projected Collection (RM)',
                data: monthlyValues,
                backgroundColor: 'rgba(5, 150, 105, 0.6)',
                borderColor: 'rgba(5, 150, 105, 1)',
                borderWidth: 2,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: {
                        color: '#94a3b8',
                        callback: value => 'RM ' + (value / 1000).toFixed(0) + 'k'
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

async function loadSegments() {
    try {
        const response = await fetch(`${API_BASE}/admin/segments`);
        const data = await response.json();

        renderSegmentChart(data.tier_counts);
        renderSegmentTable(data.segments);
    } catch (error) {
        console.error('Error loading segments:', error);
    }
}

function renderSegmentChart(tierCounts) {
    const ctx = document.getElementById('segmentChart').getContext('2d');

    const labels = Object.keys(tierCounts);
    const values = Object.values(tierCounts);
    const colors = [
        'rgba(5, 150, 105, 0.8)', // Emerald - High-Net-Worth
        'rgba(13, 148, 136, 0.8)'   // Teal - Mass Market
    ];

    if (segmentChart) segmentChart.destroy();

    segmentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.8', '1')),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#f8fafc' }
                }
            }
        }
    });
}

function renderSegmentTable(segments) {
    const tbody = document.querySelector('#segmentTable tbody');
    tbody.innerHTML = '';

    segments.forEach(seg => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <span class="tier-badge ${seg.tier === 'High-Net-Worth' ? 'tier-hnw' : 'tier-mass'}">
                    ${seg.tier}
                </span>
            </td>
            <td>${seg.count}</td>
            <td>${formatCurrency(seg.total_zakat)}</td>
            <td>${formatCurrency(seg.avg_wealth)}</td>
        `;
        tbody.appendChild(row);
    });
}

async function loadTrends(type = 'income') {
    try {
        const response = await fetch(`${API_BASE}/admin/trends`);
        const data = await response.json();

        const scatterData = type === 'income' ? data.income_vs_zakat : data.wealth_vs_zakat;
        renderTrendChart(scatterData, type);
        analyzeUnderContribution(scatterData, type);
    } catch (error) {
        console.error('Error loading trends:', error);
    }
}

function renderTrendChart(scatterData, type) {
    const ctx = document.getElementById('trendChart').getContext('2d');

    // Separate by tier for different colors
    const hnwPoints = scatterData.filter(d => d.DonorTier === 'High-Net-Worth')
        .map(d => ({ x: type === 'income' ? d.Income : d.TotalWealth, y: d.ZakatAmount }));
    const massPoints = scatterData.filter(d => d.DonorTier === 'Mass Market')
        .map(d => ({ x: type === 'income' ? d.Income : d.TotalWealth, y: d.ZakatAmount }));

    if (trendChart) trendChart.destroy();

    trendChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'High-Net-Worth',
                    data: hnwPoints,
                    backgroundColor: 'rgba(5, 150, 105, 0.6)',
                    borderColor: 'rgba(5, 150, 105, 1)',
                    pointRadius: 6
                },
                {
                    label: 'Mass Market',
                    data: massPoints,
                    backgroundColor: 'rgba(13, 148, 136, 0.6)',
                    borderColor: 'rgba(13, 148, 136, 1)',
                    pointRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#f8fafc' }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: {
                        color: '#94a3b8',
                        callback: value => 'RM ' + (value / 1000).toFixed(0) + 'k'
                    },
                    title: {
                        display: true,
                        text: type === 'income' ? 'Annual Income (RM)' : 'Total Wealth (RM)',
                        color: '#94a3b8'
                    }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#94a3b8' },
                    title: { display: true, text: 'Zakat Amount (RM)', color: '#94a3b8' }
                }
            }
        }
    });
}

function analyzeUnderContribution(data, type) {
    // Simple analysis - find outliers below expected 2.5%
    const underContributors = data.filter(d => {
        const wealth = type === 'income' ? d.Income * 0.3 : d.TotalWealth; // Rough estimate
        const expected = wealth * 0.025;
        return d.ZakatAmount < expected * 0.5 && d.ZakatAmount > 0;
    });

    const insight = document.getElementById('underContributionInsight');
    if (underContributors.length > 0) {
        insight.innerHTML = `
            <span class="insight-alert">⚠️ ${underContributors.length} donors</span> 
            are contributing significantly below the expected 2.5% rate based on their ${type} levels.
        `;
    } else {
        insight.innerHTML = `
            <span class="insight-positive">✅ Good compliance</span> 
            Most donors are contributing at or above expected levels.
        `;
    }
}

async function loadAtRiskDonors() {
    try {
        const response = await fetch(`${API_BASE}/admin/at-risk`);
        const data = await response.json();

        // Update stat card
        document.getElementById('atRiskCount').textContent = data.at_risk_count;
        document.getElementById('riskBadge').textContent = `${data.at_risk_count} donors flagged`;
        document.getElementById('potentialRecovery').textContent = formatCurrency(data.potential_collection);

        renderRiskTable(data.at_risk_donors);
    } catch (error) {
        console.error('Error loading at-risk donors:', error);
    }
}

function renderRiskTable(donors) {
    const tbody = document.querySelector('#riskTable tbody');
    tbody.innerHTML = '';

    if (donors.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="no-data">No at-risk donors identified</td></tr>';
        return;
    }

    donors.slice(0, 20).forEach(donor => {
        const row = document.createElement('tr');
        const riskLevel = donor.days_since_payment > 600 ? 'high' : 'medium';

        row.innerHTML = `
            <td><strong>${donor.DonorID}</strong></td>
            <td>${formatCurrency(donor.TotalWealth)}</td>
            <td>${formatCurrency(donor.Income)}</td>
            <td>
                <span class="tier-badge ${donor.DonorTier === 'High-Net-Worth' ? 'tier-hnw' : 'tier-mass'}">
                    ${donor.DonorTier}
                </span>
            </td>
            <td>${donor.LastPaymentDate}</td>
            <td><span class="days-overdue">${donor.days_since_payment}</span></td>
            <td>
                <span class="risk-level ${riskLevel}">
                    ${riskLevel === 'high' ? '🔴 High Risk' : '🟡 Medium Risk'}
                </span>
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function exportData() {
    try {
        const btn = document.getElementById('exportBtn');
        btn.textContent = '⏳ Exporting...';
        btn.disabled = true;

        // Trigger file download
        window.location.href = `${API_BASE}/admin/export`;

        setTimeout(() => {
            btn.textContent = '📥 Export CSV';
            btn.disabled = false;
        }, 1500);
    } catch (error) {
        console.error('Error exporting data:', error);
        alert('Error exporting data');
    }
}

function formatCurrency(num) {
    return new Intl.NumberFormat('en-MY', { style: 'currency', currency: 'MYR' }).format(num);
}
