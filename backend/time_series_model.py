"""
Time-Series Forecasting Model for Zakat Collection Analytics.

This module implements time-series forecasting using Prophet (from Meta/Facebook)
to predict future Zakat collection trends based on historical data.

Features:
1. Historical data generation with realistic seasonal patterns
2. Prophet model training for time-series forecasting
3. Forecast generation with confidence intervals
4. Seasonal decomposition (Ramadan, year-end patterns)

Assignment Requirement: "Time-series forecasting using machine learning algorithms"
"""

import json
import os
import pickle
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Prophet import with fallback
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    try:
        from fbprophet import Prophet
        PROPHET_AVAILABLE = True
    except ImportError:
        PROPHET_AVAILABLE = False
        print("Warning: Prophet not installed. Using fallback linear forecasting.")


# ============== CONFIGURATION ==============

# Hijri calendar Ramadan approximate dates (for seasonal patterns)
RAMADAN_MONTHS = {
    2020: 4,   # April-May 2020
    2021: 4,   # April-May 2021
    2022: 4,   # April 2022
    2023: 3,   # March-April 2023
    2024: 3,   # March 2024
    2025: 2,   # February-March 2025
}

# Seasonal multipliers
RAMADAN_BOOST = 2.5      # 2.5x during Ramadan
YEAR_END_BOOST = 1.3     # 1.3x in December
NORMAL_VARIATION = 0.15  # 15% random variation


# ============== HISTORICAL DATA GENERATION ==============

def generate_historical_data(start_year: int = 2020, end_year: int = 2024) -> pd.DataFrame:
    """
    Generate realistic historical monthly Zakat collection data.
    
    Includes patterns for:
    - Overall growth trend (10-15% yearly)
    - Ramadan spike (collection increases significantly)
    - Year-end increase (tax planning, charitable giving)
    - Random monthly variation
    
    Args:
        start_year: First year of historical data
        end_year: Last year of historical data
        
    Returns:
        DataFrame with columns: ds (date), y (collection amount)
    """
    np.random.seed(42)  # For reproducibility
    
    data = []
    base_monthly = 150000  # Base monthly collection: RM 150,000
    
    for year in range(start_year, end_year + 1):
        # Yearly growth factor (10-15% per year from base)
        years_from_start = year - start_year
        growth_factor = 1 + (0.12 * years_from_start)  # 12% yearly growth
        
        ramadan_month = RAMADAN_MONTHS.get(year, 4)
        
        for month in range(1, 13):
            # Base amount with growth
            amount = base_monthly * growth_factor
            
            # Ramadan boost (applies to Ramadan month and the following month)
            if month == ramadan_month or month == ramadan_month + 1:
                amount *= RAMADAN_BOOST
            
            # Year-end boost (November-December)
            elif month in [11, 12]:
                amount *= YEAR_END_BOOST
            
            # Add random variation
            variation = 1 + np.random.uniform(-NORMAL_VARIATION, NORMAL_VARIATION)
            amount *= variation
            
            # Create date
            date = datetime(year, month, 1)
            
            data.append({
                'ds': date,
                'y': round(amount, 2)
            })
    
    df = pd.DataFrame(data)
    return df


def save_historical_data(df: pd.DataFrame, filepath: str = "historical_collections.csv"):
    """Save generated historical data to CSV."""
    df.to_csv(filepath, index=False)
    print(f"Historical data saved to {filepath}")


# ============== PROPHET MODEL ==============

class ZakatTimeSeriesModel:
    """
    Time-series forecasting model for Zakat collections using Prophet.
    
    Prophet is designed for business time-series with:
    - Strong seasonal effects
    - Multiple seasonality (yearly, monthly)
    - Missing data/outliers
    - Trend changes
    """
    
    def __init__(self):
        self.model = None
        self.is_fitted = False
        self.forecast = None
        
    def train(self, df: pd.DataFrame):
        """
        Train Prophet model on historical data.
        
        Args:
            df: DataFrame with 'ds' (date) and 'y' (value) columns
        """
        if not PROPHET_AVAILABLE:
            print("Prophet not available, using fallback method")
            self._train_fallback(df)
            return
        
        print("Training Prophet model...")
        
        # Initialize Prophet with custom seasonality
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,  # Monthly data, no weekly pattern
            daily_seasonality=False,
            seasonality_mode='multiplicative',  # Better for growth patterns
            changepoint_prior_scale=0.05,  # Flexibility for trend changes
        )
        
        # Add custom seasonality for Ramadan (approximately)
        # Using ~29.5 day lunar month cycle
        self.model.add_seasonality(
            name='ramadan_cycle',
            period=354.37,  # Lunar year in days
            fourier_order=3
        )
        
        # Fit the model
        self.model.fit(df)
        self.is_fitted = True
        print("Prophet model trained successfully!")
        
    def _train_fallback(self, df: pd.DataFrame):
        """Fallback training using simple linear regression."""
        from sklearn.linear_model import LinearRegression
        
        df = df.copy()
        df['month_num'] = range(len(df))
        
        self.fallback_model = LinearRegression()
        X = df[['month_num']].values
        y = df['y'].values
        self.fallback_model.fit(X, y)
        
        self.last_month_num = len(df) - 1
        self.is_fitted = True
        print("Fallback linear model trained!")
        
    def predict(self, periods: int = 12) -> pd.DataFrame:
        """
        Generate forecast for future periods.
        
        Args:
            periods: Number of months to forecast
            
        Returns:
            DataFrame with forecast and confidence intervals
        """
        if not self.is_fitted:
            raise ValueError("Model not trained. Call train() first.")
        
        if PROPHET_AVAILABLE and self.model is not None:
            # Create future dataframe
            future = self.model.make_future_dataframe(periods=periods, freq='MS')
            
            # Generate forecast
            self.forecast = self.model.predict(future)
            
            # Return relevant columns
            result = self.forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
            result.columns = ['date', 'forecast', 'lower_bound', 'upper_bound']
            
            return result
        else:
            return self._predict_fallback(periods)
    
    def _predict_fallback(self, periods: int) -> pd.DataFrame:
        """Fallback prediction using linear model."""
        future_months = np.arange(
            self.last_month_num + 1, 
            self.last_month_num + 1 + periods
        ).reshape(-1, 1)
        
        predictions = self.fallback_model.predict(future_months)
        
        # Generate dates
        last_date = datetime(2024, 12, 1)
        dates = [last_date + timedelta(days=30*i) for i in range(1, periods + 1)]
        
        result = pd.DataFrame({
            'date': dates,
            'forecast': predictions,
            'lower_bound': predictions * 0.85,  # 15% lower
            'upper_bound': predictions * 1.15   # 15% upper
        })
        
        return result
    
    def get_components(self) -> dict:
        """Get trend and seasonal components from the model."""
        if not PROPHET_AVAILABLE or self.forecast is None:
            return {}
        
        return {
            'trend': self.forecast['trend'].tolist(),
            'yearly': self.forecast.get('yearly', pd.Series()).tolist(),
        }
    
    def save(self, filepath: str = "forecast_model.pkl"):
        """Save trained model to file."""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"Model saved to {filepath}")
    
    @staticmethod
    def load(filepath: str = "forecast_model.pkl") -> 'ZakatTimeSeriesModel':
        """Load trained model from file."""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


# ============== FORECAST API HELPERS ==============

def get_forecast_data(periods: int = 12) -> dict:
    """
    Get forecast data for API response.
    
    Returns dict with:
    - historical: Past monthly collections
    - forecast: Future predictions with confidence intervals
    - summary: Key metrics
    """
    # Generate or load historical data
    hist_path = "historical_collections.csv"
    if os.path.exists(hist_path):
        historical_df = pd.read_csv(hist_path, parse_dates=['ds'])
    else:
        historical_df = generate_historical_data()
        save_historical_data(historical_df, hist_path)
    
    # Train or load model
    model_path = "forecast_model.pkl"
    if os.path.exists(model_path):
        try:
            model = ZakatTimeSeriesModel.load(model_path)
        except:
            model = ZakatTimeSeriesModel()
            model.train(historical_df)
            model.save(model_path)
    else:
        model = ZakatTimeSeriesModel()
        model.train(historical_df)
        model.save(model_path)
    
    # Generate forecast
    forecast_df = model.predict(periods)
    
    # Prepare response
    historical_data = [
        {
            'date': row['ds'].strftime('%Y-%m-%d'),
            'amount': round(row['y'], 2)
        }
        for _, row in historical_df.iterrows()
    ]
    
    forecast_data = [
        {
            'date': row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])[:10],
            'forecast': round(row['forecast'], 2),
            'lower_bound': round(row['lower_bound'], 2),
            'upper_bound': round(row['upper_bound'], 2)
        }
        for _, row in forecast_df.tail(periods).iterrows()
    ]
    
    # Calculate summary metrics
    total_historical = historical_df['y'].sum()
    avg_monthly = historical_df['y'].mean()
    total_forecast = forecast_df.tail(periods)['forecast'].sum()
    
    # Year-over-year growth
    last_year = historical_df.tail(12)['y'].sum()
    prev_year = historical_df.iloc[-24:-12]['y'].sum() if len(historical_df) >= 24 else last_year
    yoy_growth = ((last_year - prev_year) / prev_year * 100) if prev_year > 0 else 0
    
    return {
        'historical': historical_data,
        'forecast': forecast_data,
        'summary': {
            'total_historical': round(total_historical, 2),
            'average_monthly': round(avg_monthly, 2),
            'total_forecast_12m': round(total_forecast, 2),
            'yoy_growth_percent': round(yoy_growth, 1),
            'forecast_periods': periods
        },
        'model_info': {
            'type': 'Prophet' if PROPHET_AVAILABLE else 'Linear Regression (Fallback)',
            'seasonality': ['yearly', 'ramadan_cycle'] if PROPHET_AVAILABLE else ['none'],
            'confidence_level': 0.8
        }
    }


# ============== MAIN ==============

if __name__ == "__main__":
    print("=" * 50)
    print("TIME-SERIES FORECASTING MODEL")
    print("=" * 50)
    
    # Generate historical data
    print("\n1. Generating historical data...")
    historical_df = generate_historical_data()
    save_historical_data(historical_df)
    print(f"   Generated {len(historical_df)} months of data")
    print(historical_df.tail())
    
    # Train model
    print("\n2. Training time-series model...")
    model = ZakatTimeSeriesModel()
    model.train(historical_df)
    
    # Generate forecast
    print("\n3. Generating 12-month forecast...")
    forecast = model.predict(12)
    print(forecast)
    
    # Save model
    model.save()
    
    # Test API helper
    print("\n4. Testing API response format...")
    api_response = get_forecast_data(12)
    print(f"   Historical records: {len(api_response['historical'])}")
    print(f"   Forecast records: {len(api_response['forecast'])}")
    print(f"   Summary: {api_response['summary']}")
    
    print("\n✅ Time-series model ready!")
