import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

def train_model():
    # Load data
    try:
        df = pd.read_csv('mock_zakat_data.csv')
    except FileNotFoundError:
        print("Error: mock_zakat_data.csv not found. Please run data_generator.py first.")
        return

    # Features and Target - now using expanded feature set
    feature_columns = ['Age', 'Income', 'Savings', 'GoldValue', 'InvestmentValue', 
                      'FamilySize', 'EmploymentStatus', 'PreviousContributionScore']
    
    X = df[feature_columns]
    y = df['ZakatAmount']

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train Model
    print("Training Random Forest Regressor with expanded features...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Convert test predictions
    predictions = model.predict(X_test)
    
    # Evaluate
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    
    print(f"Model Training Completed.")
    print(f"Mean Absolute Error: {mae:.2f}")
    print(f"R2 Score: {r2:.2f}")
    print(f"Features used: {feature_columns}")

    # Save model
    with open('zakat_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    print("Model saved to zakat_model.pkl")

if __name__ == "__main__":
    train_model()
