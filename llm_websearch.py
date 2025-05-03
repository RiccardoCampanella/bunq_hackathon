import json
from openai import OpenAI

def filter_user_data(data, user_id):
    """Filter dataset for specific user from dictionary structure"""
    if not isinstance(data, dict):
        raise ValueError("Invalid data structure - expected user dictionary")
    
    if user_id not in data:
        raise ValueError(f"No user found with ID: {user_id}")
    
    return data[user_id]

def load_regression_predictions(user_id):
    """Load and filter regression predictions for specific user"""
    try:
        with open('regression_values.json') as f:
            all_predictions = json.load(f)
    except FileNotFoundError:
        raise ValueError("Regression data file not found")
    
    user_predictions = [p for p in all_predictions if p['user_id'] == user_id]
    if not user_predictions:
        raise ValueError(f"No regression data for user {user_id}")
    
    return {p['category']: p['predicted_increase_probability'] for p in user_predictions}

def create_recommendations_prompt(user_data):
    """Generate prompt for financial recommendations with strict JSON formatting"""
    return f"""STRICT JSON ANALYSIS REQUEST:
You MUST respond with VALID JSON ONLY using this EXACT structure:
{{
  "key_metrics": {{
    "total_monthly_obligations": "calculated_number",
    "largest_expense_category": "category_name_string",
    "financial_stability_score": "number_0-100"
  }},
  "observations": ["array_of_strings"],
  "recommendations": ["array_of_strings"]
}}

User Financial Data:
{json.dumps(user_data, indent=2)}

CRITICAL INSTRUCTIONS:
1. Output ONLY the JSON object
2. No markdown formatting
3. No additional text
4. Use double quotes ONLY
5. Escape special characters
6. Maintain exact key names
7. Financial_stability_score must be 0-100 integer

Example VALID response:
{{
  "key_metrics": {{
    "total_monthly_obligations": 4150,
    "largest_expense_category": "Rent",
    "financial_stability_score": 68
  }},
  "observations": [
    "High rental costs consuming 48% of income",
    "Diversified subscription portfolio"
  ],
  "recommendations": [
    "Negotiate rent terms",
    "Audit subscription services"
  ]
}}"""

def create_predictions_prompt(user_data, regression_data):
    """Generate predictions prompt with explicit formatting rules"""
    return f"""STRICT PREDICTION REQUEST:
You MUST respond with VALID JSON ONLY using this EXACT structure:
{{
  "predictions": {{
    "status_quo": {{
      "salary_trend": "20-30 word_description", 
      "subscription_trend": "20-30 word_description",
      "rent_trend": "20-30 word_description"
    }},
    "with_recommendations": {{
      "salary_trend": "20-30 word_description",
      "subscription_trend": "20-30 word_description",
      "rent_trend": "20-30 word_description"
    }},
    "regression_based": {{
      "salary_increase_probability": {regression_data.get('SALARY', 0)},
      "subscription_increase_probability": {regression_data.get('SUBSCRIPTIONS', 0)},
      "rent_increase_probability": {regression_data.get('RENT_AND_UTILITIES', 0)}
    }}
  }}
}}

User Financial Data:
{json.dumps(user_data, indent=2)}

Regression Probabilities:
{json.dumps(regression_data, indent=2)}

CRITICAL INSTRUCTIONS:
1. Output ONLY the JSON object - no commentary
2. Maintain EXACT key names and structure
3. Use double quotes ONLY
4. Trend descriptions must be 20-30 words
5. Escape special characters
6. No markdown formatting
7. Always provide growth and decline in percantages
"""

def query_llama(prompt):
    """Query NVIDIA's Llama model"""
    client = OpenAI(
        api_key="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",
        base_url="https://integrate.api.nvidia.com/v1"
    )

    response = client.chat.completions.create(
        model="meta/llama3-70b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse model response: {e}")

def main(target_user_id="558"):
    try:
        # Load and prepare data
        with open('llm_input_data.json') as f:
            raw_data = json.load(f)
        user_data = filter_user_data(raw_data, target_user_id)
        regression_data = load_regression_predictions(target_user_id)
        
        # First completion - Core analysis
        rec_prompt = create_recommendations_prompt(user_data)
        analysis = query_llama(rec_prompt)
        print(f"{analysis}")
        # Second completion - Predictions
        pred_prompt = create_predictions_prompt(user_data, regression_data)
        predictions = query_llama(pred_prompt)
        
        # Merge results
        analysis.update(predictions)
        
        # Add scraping recommendations
        analysis['recommendations'] += [
            "SCRAPE: Rental listings in transaction areas <€2500/mo",
            "SCRAPE: High-salary positions in international finance",
            "SCRAPE: Subscription alternatives for frequent categories"
        ]
        
        # Save results
        with open('financial_analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"Analysis complete for user {target_user_id}. Results saved.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Common fixes: Check data files exist and contain required user ID")

if __name__ == '__main__':
    main()