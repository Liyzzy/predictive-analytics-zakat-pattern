# Predictive Zakat Analytics

A web application to analyze Zakat contribution patterns and predict potential Zakat amounts based on donor profiles.
Built for the group assignment on Predictive Analytics.

## Features
- **Dashboard**: Visualizes donor demographics and contribution trends.
- **Prediction**: Uses Machine Learning (Random Forest) to estimate Zakat.
- **Simulation**: Generates realistic mock data for analysis.

## Setup
1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python data_generator.py
   python model.py
   python app.py
   ```

2. **Frontend**:
   - Open `frontend/index.html` in your browser.

## Technologies
- **Backend**: Python, Flask, Pandas, Scikit-Learn
- **Frontend**: HTML5, CSS3 (Modern/Glassmorphism), JavaScript, Chart.js
