# Predictive Zakat Analytics

A web application to analyze Zakat contribution patterns and predict potential Zakat amounts based on donor profiles.
Built for the group assignment on Predictive Analytics.

## Features
- **Dashboard**: Visualizes donor demographics and contribution trends.
- **Prediction**: Uses Machine Learning (Random Forest) to estimate Zakat.
- **Simulation**: Generates realistic mock data for analysis.
- **Time-Series**: Forecasts aggregate collection trends using Prophet.
- **Persistence**: Remembers user profiles and financial data.

## Setup Instructions

Follow these steps to set up the project locally.

### 1. Backend Setup

First, ensure you have Python 3.12 installed.

**Step 1: Create Virtual Environment**
```bash
cd backend
python3.12 -m venv venv
```

**Step 2: Activate Virtual Environment**
- On macOS/Linux:
  ```bash
  source venv/bin/activate
  ```
- On Windows:
  ```bash
  venv\Scripts\activate
  ```

**Step 3: Install Dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Step 4: Generate Data & Train Models**
```bash
# Generate mock donor data (including anonymization)
python data_generator.py

# Train the Machine Learning model
python model.py

# (Optional) Test time-series model
python time_series_model.py
```

**Step 5: Run the Server**
```bash
python app.py
```
*The server will start at `http://localhost:5000`*

### 2. Frontend Setup

The frontend is built with pure HTML/CSS/JS and connects to the Flask API.

- Open `frontend/index.html` in your web browser.
- Or servce it using a simple HTTP server:
  ```bash
  cd ../frontend
  npx serve .
  ```

## Technologies
- **Backend**: Python 3.12, Flask, Pandas, Scikit-Learn, Prophet
- **Frontend**: HTML5, CSS3 (Modern/Glassmorphism), JavaScript, Chart.js, Phosphor Icons
