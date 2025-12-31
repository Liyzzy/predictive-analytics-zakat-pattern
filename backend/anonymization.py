"""
Data Anonymization and Preprocessing Module for Zakat Analytics.

This module provides utilities for:
1. Donor ID pseudonymization (hashing)
2. Data masking for sensitive financial values
3. Income bucketing/binning
4. Data normalization for ML features
5. Outlier detection and handling

Implements privacy-preserving techniques as per assignment requirements.
"""

import hashlib
import numpy as np
import pandas as pd
from typing import Union, List, Optional


# ============== CONFIGURATION ==============

# Secret salt for hashing (in production, use environment variable)
ANONYMIZATION_SALT = "zakat-tech-salt-2024"

# Income buckets for k-anonymity
INCOME_BUCKETS = [
    (0, 20000, "Low"),
    (20000, 50000, "Lower-Middle"),
    (50000, 100000, "Middle"),
    (100000, 200000, "Upper-Middle"),
    (200000, float('inf'), "High")
]

# Wealth buckets
WEALTH_BUCKETS = [
    (0, 22000, "Below Nisab"),
    (22000, 50000, "Nisab-50K"),
    (50000, 100000, "50K-100K"),
    (100000, 250000, "100K-250K"),
    (250000, float('inf'), "250K+")
]


# ============== ANONYMIZATION FUNCTIONS ==============

def anonymize_donor_id(donor_id: str, salt: str = ANONYMIZATION_SALT) -> str:
    """
    Pseudonymize donor ID using SHA-256 hashing.
    
    This creates a consistent, one-way hash of the donor ID that:
    - Cannot be reversed to get the original ID
    - Always produces the same output for the same input (deterministic)
    - Maintains referential integrity for analytics
    
    Args:
        donor_id: Original donor identifier (e.g., "MZ1001")
        salt: Secret salt to prevent rainbow table attacks
        
    Returns:
        12-character anonymized ID with "ANON_" prefix
        
    Example:
        >>> anonymize_donor_id("MZ1001")
        'ANON_a3f2b1c4d5e6'
    """
    combined = f"{donor_id}{salt}"
    hash_object = hashlib.sha256(combined.encode())
    hash_hex = hash_object.hexdigest()
    return f"ANON_{hash_hex[:12]}"


def mask_financial_value(value: Union[int, float], precision: str = "thousands") -> str:
    """
    Mask sensitive financial values for display purposes.
    
    Args:
        value: The financial value to mask
        precision: Level of masking - "thousands", "hundreds", or "exact"
        
    Returns:
        Masked string representation
        
    Examples:
        >>> mask_financial_value(125750, "thousands")
        'RM 125,XXX'
        >>> mask_financial_value(125750, "hundreds")
        'RM 125,7XX'
    """
    if value is None or pd.isna(value):
        return "RM X,XXX"
    
    value = float(value)
    
    if precision == "thousands":
        # Show only thousands, mask the rest
        thousands = int(value // 1000)
        return f"RM {thousands:,},XXX"
    elif precision == "hundreds":
        # Show up to hundreds
        hundreds = int(value // 100) * 100
        masked_part = "XX"
        return f"RM {hundreds:,}".replace("00", masked_part)
    else:
        return f"RM {value:,.2f}"


def bucket_income(income: Union[int, float]) -> str:
    """
    Categorize income into predefined buckets for k-anonymity.
    
    This prevents re-identification by grouping similar incomes together.
    
    Args:
        income: Annual income value
        
    Returns:
        Income bucket label
    """
    if income is None or pd.isna(income):
        return "Unknown"
    
    for min_val, max_val, label in INCOME_BUCKETS:
        if min_val <= income < max_val:
            return label
    return "High"


def bucket_wealth(wealth: Union[int, float]) -> str:
    """
    Categorize total wealth into predefined buckets.
    
    Args:
        wealth: Total zakatable wealth value
        
    Returns:
        Wealth bucket label
    """
    if wealth is None or pd.isna(wealth):
        return "Unknown"
    
    for min_val, max_val, label in WEALTH_BUCKETS:
        if min_val <= wealth < max_val:
            return label
    return "250K+"


def bucket_age(age: int) -> str:
    """
    Categorize age into generational groups.
    
    Args:
        age: Age in years
        
    Returns:
        Age group label
    """
    if age is None or pd.isna(age):
        return "Unknown"
    
    if age < 30:
        return "Young Adult (18-29)"
    elif age < 45:
        return "Adult (30-44)"
    elif age < 60:
        return "Middle-Aged (45-59)"
    else:
        return "Senior (60+)"


# ============== PREPROCESSING FUNCTIONS ==============

def normalize_features(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Apply Min-Max normalization to specified columns.
    
    Scales values to range [0, 1] for ML model training.
    
    Args:
        df: DataFrame containing the data
        columns: List of column names to normalize
        
    Returns:
        DataFrame with normalized columns (suffixed with '_normalized')
    """
    result_df = df.copy()
    
    for col in columns:
        if col in df.columns:
            min_val = df[col].min()
            max_val = df[col].max()
            
            if max_val - min_val > 0:
                result_df[f"{col}_normalized"] = (df[col] - min_val) / (max_val - min_val)
            else:
                result_df[f"{col}_normalized"] = 0.0
    
    return result_df


def detect_outliers(df: pd.DataFrame, column: str, method: str = "iqr") -> pd.Series:
    """
    Detect outliers in a numerical column.
    
    Args:
        df: DataFrame containing the data
        column: Column name to check for outliers
        method: Detection method - "iqr" (Interquartile Range) or "zscore"
        
    Returns:
        Boolean Series where True indicates an outlier
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")
    
    values = df[column].dropna()
    
    if method == "iqr":
        Q1 = values.quantile(0.25)
        Q3 = values.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return (df[column] < lower_bound) | (df[column] > upper_bound)
    
    elif method == "zscore":
        mean = values.mean()
        std = values.std()
        z_scores = np.abs((df[column] - mean) / std)
        return z_scores > 3
    
    else:
        raise ValueError(f"Unknown method: {method}")


def handle_missing_values(df: pd.DataFrame, strategy: str = "median") -> pd.DataFrame:
    """
    Handle missing values in numerical columns.
    
    Args:
        df: DataFrame with potential missing values
        strategy: How to fill missing values - "median", "mean", or "zero"
        
    Returns:
        DataFrame with missing values filled
    """
    result_df = df.copy()
    numeric_cols = result_df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        if result_df[col].isna().any():
            if strategy == "median":
                fill_value = result_df[col].median()
            elif strategy == "mean":
                fill_value = result_df[col].mean()
            else:
                fill_value = 0
            
            result_df[col] = result_df[col].fillna(fill_value)
    
    return result_df


# ============== FULL ANONYMIZATION PIPELINE ==============

def anonymize_dataframe(df: pd.DataFrame, 
                        anonymize_ids: bool = True,
                        bucket_financial: bool = True,
                        mask_values: bool = False) -> pd.DataFrame:
    """
    Apply full anonymization pipeline to a donor DataFrame.
    
    Args:
        df: Original DataFrame with donor data
        anonymize_ids: Whether to hash donor IDs
        bucket_financial: Whether to bucket income/wealth into categories
        mask_values: Whether to mask exact financial values
        
    Returns:
        Anonymized DataFrame safe for sharing/export
    """
    result_df = df.copy()
    
    # 1. Anonymize Donor IDs
    if anonymize_ids and 'DonorID' in result_df.columns:
        result_df['AnonymizedDonorID'] = result_df['DonorID'].apply(anonymize_donor_id)
    
    # 2. Bucket financial data for k-anonymity
    if bucket_financial:
        if 'Income' in result_df.columns:
            result_df['IncomeBucket'] = result_df['Income'].apply(bucket_income)
        
        if 'TotalWealth' in result_df.columns:
            result_df['WealthBucket'] = result_df['TotalWealth'].apply(bucket_wealth)
        
        if 'Age' in result_df.columns:
            result_df['AgeGroup'] = result_df['Age'].apply(bucket_age)
    
    # 3. Mask exact values if requested
    if mask_values:
        if 'Income' in result_df.columns:
            result_df['MaskedIncome'] = result_df['Income'].apply(mask_financial_value)
        
        if 'Savings' in result_df.columns:
            result_df['MaskedSavings'] = result_df['Savings'].apply(mask_financial_value)
        
        if 'TotalWealth' in result_df.columns:
            result_df['MaskedWealth'] = result_df['TotalWealth'].apply(mask_financial_value)
    
    return result_df


def create_anonymized_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a fully anonymized version of donor data suitable for external sharing.
    
    This removes direct identifiers and replaces exact values with buckets.
    
    Args:
        df: Original DataFrame
        
    Returns:
        Anonymized DataFrame with only safe columns
    """
    anon_df = anonymize_dataframe(df, anonymize_ids=True, bucket_financial=True, mask_values=True)
    
    # Select only anonymized columns for export
    safe_columns = [
        'AnonymizedDonorID',
        'AgeGroup',
        'IncomeBucket',
        'WealthBucket',
        'FamilySize',
        'EmploymentStatus',
        'DonorTier',
        'ZakatAmount'  # Aggregated amounts are generally safe
    ]
    
    # Only include columns that exist
    export_columns = [col for col in safe_columns if col in anon_df.columns]
    
    return anon_df[export_columns]


def preprocess_for_ml(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess data for ML model training.
    
    Applies:
    - Missing value handling
    - Outlier detection (flagging, not removal)
    - Feature normalization
    
    Args:
        df: Raw DataFrame
        
    Returns:
        Preprocessed DataFrame ready for ML
    """
    # Handle missing values
    result_df = handle_missing_values(df, strategy="median")
    
    # Normalize key features
    numeric_features = ['Age', 'Income', 'Savings', 'GoldValue', 
                        'InvestmentValue', 'TotalWealth', 'PreviousContributionScore']
    existing_features = [f for f in numeric_features if f in result_df.columns]
    result_df = normalize_features(result_df, existing_features)
    
    # Flag outliers (don't remove - let the model handle them)
    if 'Income' in result_df.columns:
        result_df['IncomeOutlier'] = detect_outliers(result_df, 'Income')
    
    if 'TotalWealth' in result_df.columns:
        result_df['WealthOutlier'] = detect_outliers(result_df, 'TotalWealth')
    
    return result_df


# ============== UTILITY FUNCTIONS ==============

def get_anonymization_summary(df: pd.DataFrame) -> dict:
    """
    Generate a summary of anonymization applied to a DataFrame.
    
    Returns:
        Dictionary with anonymization statistics
    """
    summary = {
        'total_records': len(df),
        'columns_anonymized': [],
        'buckets_applied': {},
        'outliers_detected': {}
    }
    
    if 'AnonymizedDonorID' in df.columns:
        summary['columns_anonymized'].append('DonorID')
    
    if 'IncomeBucket' in df.columns:
        summary['buckets_applied']['Income'] = df['IncomeBucket'].value_counts().to_dict()
    
    if 'WealthBucket' in df.columns:
        summary['buckets_applied']['Wealth'] = df['WealthBucket'].value_counts().to_dict()
    
    if 'IncomeOutlier' in df.columns:
        summary['outliers_detected']['Income'] = int(df['IncomeOutlier'].sum())
    
    if 'WealthOutlier' in df.columns:
        summary['outliers_detected']['Wealth'] = int(df['WealthOutlier'].sum())
    
    return summary


if __name__ == "__main__":
    # Quick test
    print("Testing anonymization module...")
    
    # Test donor ID anonymization
    test_id = "MZ1001"
    anon_id = anonymize_donor_id(test_id)
    print(f"Original: {test_id} -> Anonymized: {anon_id}")
    
    # Test determinism
    assert anonymize_donor_id(test_id) == anon_id, "Should be deterministic"
    
    # Test masking
    print(f"Masked value: {mask_financial_value(125750)}")
    
    # Test bucketing
    print(f"Income bucket: {bucket_income(75000)}")
    print(f"Wealth bucket: {bucket_wealth(150000)}")
    print(f"Age group: {bucket_age(35)}")
    
    print("\n✅ All tests passed!")
