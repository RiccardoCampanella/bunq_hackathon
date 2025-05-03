import json
from collections import defaultdict

# Load all datasets
with open('rental_analysis_report.json') as f:
    rental_data = json.load(f)

with open('subscription_analysis.json') as f:
    subscription_data = json.load(f)

with open('grouped_salary_transactions.json') as f:
    salary_data = json.load(f)

# Create master dictionary
user_records = defaultdict(lambda: {
    'rental_info': {},
    'subscription_info': {},
    'salary_transactions': []
})

# Populate rental info
for user_id, data in rental_data['user_analysis'].items():
    user_records[user_id]['rental_info'] = {
        'financial_metrics': {
            'total_transactions': data['total_transactions'],
            'total_amount': data['total_amount'],
            'country_distribution': data['country_distribution']
        },
        'geographical_insights': {
            'cities': list(data['city_distribution'].keys()),
            'transaction_spread_km': data['spread_km']
        }
    }

# Populate subscription info
for user_id, data in subscription_data['user_breakdown'].items():
    user_records[user_id]['subscription_info'] = {
        'total_subscriptions': data['total_subscriptions'],
        'monthly_cost_breakdown': data['total_monthly_cost'],
        #'trends': {
            #'most_volatile': data['trend_analysis']['most_volatile'],
            #'top_increased': data['trend_analysis']['top_increased']
        #}
    }

# Populate salary data
for user_id, transactions in salary_data.items():
    user_records[user_id]['salary_transactions'] = [{
        'timestamp': t['updated_timestamp'],
        'amount': t['amount'],
        'financial_metadata': {
            'currency': t['currency'],
            'transaction_type': t['transaction_type'],
            'recommendations': t['recommendations_category']
        },
        'counterparty': t['counterparty_name'],
        'category_tags': t['tags'].split(',')
    } for t in transactions]

# Convert to regular dict and save
combined_data = dict(user_records)
with open('llm_input_data.json', 'w') as f:
    json.dump(combined_data, f, indent=2)