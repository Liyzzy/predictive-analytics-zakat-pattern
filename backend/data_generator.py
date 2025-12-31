import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Import anonymization utilities
from anonymization import (
    anonymize_donor_id,
    bucket_income,
    bucket_wealth,
    bucket_age,
    preprocess_for_ml,
    get_anonymization_summary
)

def generate_mock_data(num_samples=500):
    """
    Generates synthetic data for Zakat analytics.
    Features:
    - Age: 20-80
    - Income: Annual Income (RM)
    - Savings: Cash savings (RM)
    - GoldValue: Gold assets value (RM)
    - InvestmentValue: Investment portfolios (RM)
    - FamilySize: 1-10
    - EmploymentStatus: 0 (Unemployed), 1 (Employed), 2 (Self-Employed)
    - PreviousContributionScore: Score 0-100 (Frequency/Reliability)
    - LastPaymentDate: Date of last Zakat payment
    - HaulStartDate: Date when wealth reached Nisab
    - DonorTier: High-Net-Worth / Mass Market
    - ZakatAmount: Target variable
    """
    np.random.seed(42)
    random.seed(42)

    # Current Nisab rate approximation (RM) - based on gold price
    NISAB_THRESHOLD = 22000  # ~85 grams of gold at current prices

    data = []
    
    for i in range(num_samples):
        age = random.randint(22, 75)
        
        # Base income influenced by age and employment
        employment = random.choice([0, 1, 1, 1, 2])  # Higher chance of being employed
        
        if employment == 0:
            income = random.randint(0, 5000)
            savings = random.randint(0, 2000)
            gold_value = random.randint(0, 3000)
            investment = 0
        elif employment == 1:
            income = random.randint(20000, 150000) + (age * 500)
            savings = random.randint(5000, 80000)
            gold_value = random.randint(0, 30000)
            investment = random.randint(0, 100000)
        else:
            income = random.randint(15000, 300000) + (age * 200)
            savings = random.randint(10000, 150000)
            gold_value = random.randint(0, 50000)
            investment = random.randint(0, 200000)

        family_size = random.randint(1, 9)
        
        # Calculate total wealth (Zakatable assets)
        total_wealth = savings + gold_value + investment
        
        # Previous history score
        prev_history = random.randint(0, 100)
        
        # Generate dates
        today = datetime.now()
        haul_start = today - timedelta(days=random.randint(30, 400))
        
        # Last payment - some users haven't paid recently (at-risk)
        if random.random() < 0.15:  # 15% are at-risk (no recent payment)
            last_payment = today - timedelta(days=random.randint(400, 800))
        else:
            last_payment = today - timedelta(days=random.randint(1, 365))
        
        # Determine donor tier based on total wealth
        if total_wealth >= 100000:
            donor_tier = "High-Net-Worth"
        else:
            donor_tier = "Mass Market"
        
        # Calculate Zakat (2.5% of wealth above Nisab)
        if total_wealth > NISAB_THRESHOLD:
            base_zakat = total_wealth * 0.025
            # Adjust based on 'generosity' factor correlated with history
            zakat_amount = base_zakat * (0.8 + (prev_history / 200)) 
            zakat_amount = max(0, zakat_amount + np.random.normal(0, 50))
        else:
            zakat_amount = 0

        # Generate donor ID and anonymized version
        donor_id = f"MZ{1000 + i}"
        anonymized_id = anonymize_donor_id(donor_id)
        
        data.append({
            "DonorID": donor_id,
            "AnonymizedDonorID": anonymized_id,
            "Age": age,
            "AgeGroup": bucket_age(age),
            "Income": int(income),
            "IncomeBucket": bucket_income(income),
            "Savings": int(savings),
            "GoldValue": int(gold_value),
            "InvestmentValue": int(investment),
            "TotalWealth": int(total_wealth),
            "WealthBucket": bucket_wealth(total_wealth),
            "FamilySize": family_size,
            "EmploymentStatus": employment,
            "PreviousContributionScore": prev_history,
            "LastPaymentDate": last_payment.strftime("%Y-%m-%d"),
            "HaulStartDate": haul_start.strftime("%Y-%m-%d"),
            "DonorTier": donor_tier,
            "ZakatAmount": round(zakat_amount, 2)
        })

    df = pd.DataFrame(data)
    
    # Apply preprocessing for ML
    df_preprocessed = preprocess_for_ml(df)
    
    # Save full dataset (with original IDs - internal use only)
    output_path = "mock_zakat_data.csv"
    df.to_csv(output_path, index=False)
    print(f"Successfully generated {num_samples} records in {output_path}")
    
    # Save anonymized dataset (safe for sharing)
    anonymized_columns = [
        'AnonymizedDonorID', 'AgeGroup', 'IncomeBucket', 'WealthBucket',
        'FamilySize', 'EmploymentStatus', 'DonorTier', 'ZakatAmount'
    ]
    df_anonymized = df[anonymized_columns]
    df_anonymized.to_csv("mock_zakat_data_anonymized.csv", index=False)
    print(f"Also saved anonymized version: mock_zakat_data_anonymized.csv")
    
    # Print summary
    print(f"\n{'='*50}")
    print("DATA GENERATION SUMMARY")
    print(f"{'='*50}")
    print(df[['DonorID', 'AnonymizedDonorID', 'Income', 'IncomeBucket']].head())
    print(f"\nDonor Tier Distribution:")
    print(df['DonorTier'].value_counts())
    print(f"\nIncome Bucket Distribution:")
    print(df['IncomeBucket'].value_counts())
    print(f"\nAt-Risk Donors (no payment in 400+ days): {len(df[df['LastPaymentDate'] < (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')])}")
    
    # Print anonymization summary
    summary = get_anonymization_summary(df)
    print(f"\nAnonymization Summary: {summary}")


if __name__ == "__main__":
    generate_mock_data()
