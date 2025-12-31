"""
Recommendation Engine for Zakat Analytics.

This module generates personalized, actionable advice for donors based on:
1. Their Zakat Prediction (High/Low)
2. Their Financial Profile (Income vs Savings)
3. Their Consistency Score
4. Their Wealth Composition (Cash vs Gold vs Investments)
"""

def generate_recommendations(profile, prediction_result):
    """
    Generate a list of strategic recommendations based on user profile and prediction.
    
    Args:
        profile (dict): User profile data (income, savings, gold_value, etc.)
        prediction_result (dict): Result from ML model (predicted_zakat, risk_level, etc.)
        
    Returns:
        list[dict]: List of recommendations with 'icon', 'title', 'desc'.
    """
    recommendations = []
    
    # Extract values for easier logic
    income = float(profile.get('income', 0))
    savings = float(profile.get('savings', 0))
    gold = float(profile.get('gold_value', 0))
    investment = float(profile.get('investment_value', 0))
    predicted_zakat = float(prediction_result.get('predicted_zakat', 0))
    
    # Rule 1: High Income, Low Savings (Cash Flow Issue)
    # If annual income > 60k (5k/month) but savings < 10k
    if income > 60000 and savings < 10000:
        recommendations.append({
            "type": "strategy",
            "icon": "ph-trend-up",
            "title": "Optimize Cash Flow",
            "desc": "You have strong earning power but low liquidity. Consider a **monthly Zakat deduction** (PZ) to manage cash flow better."
        })
        
    # Rule 2: High Gold Assets (Gold Awareness)
    # If gold > 10k
    if gold > 10000:
        recommendations.append({
            "type": "compliance",
            "icon": "ph-coins",
            "title": "Gold Assessment",
            "desc": "Your gold assets are significant. Remember that **jewelry worn daily** is often exempt (Uruf), while stored gold is fully Zakatable."
        })
        
    # Rule 3: Investment Heavy (Investment Zakat)
    # If investment > savings
    if investment > savings and investment > 20000:
        recommendations.append({
            "type": "info",
            "icon": "ph-chart-pie-slice",
            "title": "Investment Zakat",
            "desc": "For your investment portfolio, Zakat is only due on the **principal amount** plus any realized profits, not unrealized gains."
        })
        
    # Rule 4: Borderline Nisab (Near Threshold)
    # If predicted zakat is low but positive (e.g. < RM 200)
    if 0 < predicted_zakat < 200:
        recommendations.append({
            "type": "warning",
            "icon": "ph-warning-circle",
            "title": "Near Threshold",
            "desc": "You are just above the Nisab threshold. Your obligation is sensitive to small fluctuations in savings."
        })
        
    # Rule 5: High Zakat Liability (Tax Relief)
    # If predicted zakat > RM 1000
    if predicted_zakat > 1000:
        recommendations.append({
            "type": "benefit",
            "icon": "ph-receipt",
            "title": "Tax Rebate",
            "desc": "Your Zakat payment of RM {:.0f} makes you eligible for a **100% tax rebate** on your income tax. Keep your receipt!".format(predicted_zakat)
        })

    # Default recommendation if list is empty
    if not recommendations:
        recommendations.append({
            "type": "general",
            "icon": "ph-check-circle",
            "title": "Maintain Consistency",
            "desc": "Your financial profile is balanced. Continue your consistent Zakat contributions to purify your wealth."
        })
        
    return recommendations
