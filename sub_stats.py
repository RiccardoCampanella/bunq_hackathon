import json
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

def parse_iso_datetime(dt_str):
    """Handle both formats: with and without microseconds"""
    try:
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")

def process_subscription_transactions(transactions):
    """Process transactions to extract subscription stats"""
    try:
        transactions.sort(key=lambda x: parse_iso_datetime(x['updated_timestamp']))
    except KeyError:
        return None
    
    amounts = [abs(float(t.get('amount', 0))) for t in transactions]
    dates = [parse_iso_datetime(t['updated_timestamp']) for t in transactions]
    
    changes = []
    for i in range(1, len(amounts)):
        old = amounts[i-1]
        new = amounts[i]
        if old == 0:
            change = 0
        else:
            change = ((new - old) / old) * 100
        changes.append(change)
    
    return {
        'transaction_count': len(transactions),
        'amount_history': amounts,
        'date_history': [d.isoformat() for d in dates],
        'percentage_changes': changes,
        'current_amount': amounts[-1] if amounts else 0,
        'max_amount': max(amounts) if amounts else 0,
        'min_amount': min(amounts) if amounts else 0,
        'currency': transactions[0].get('currency', '')
    }

def analyze_subscriptions(transactions):
    """Analyze subscriptions with user-specific statistics"""
    subs = [t for t in transactions if t.get('category') == 'SUBSCRIPTION']  # Fixed category
    
    analysis = {
        'total_subscriptions': len(subs),
        'active_subscriptions': 0,
        'subscription_stats': defaultdict(dict),
        'user_stats': defaultdict(dict),
        'overall_stats': {
            'average_monthly_change': 0,
            'total_monthly_cost': 0,
            'most_volatile': {'name': '', 'change': 0},
            'top_increased': {'name': '', 'increase': 0},
            'top_decreased': {'name': '', 'decrease': 0}
        },
        'monthly_trends': defaultdict(lambda: {
            'total_spend': 0,
            'subscription_count': 0,
            'new_subscriptions': 0,
            'cancellations': 0
        })
    }

    # Group transactions by counterparty and user
    grouped_counterparty = defaultdict(list)
    grouped_user = defaultdict(lambda: defaultdict(list))  # user_id -> counterparty -> transactions
    for sub in subs:
        counterparty = sub['counterparty_name'].strip().lower()
        grouped_counterparty[counterparty].append(sub)
        user_id = sub.get('owner_user_id', 'unknown')
        grouped_user[user_id][counterparty].append(sub)

    # Process counterparty-based subscriptions
    for counterparty, transactions in grouped_counterparty.items():
        processed = process_subscription_transactions(transactions)
        if not processed:
            continue
        analysis['subscription_stats'][counterparty] = processed
        
        # Update monthly trends
        for date in [parse_iso_datetime(t['updated_timestamp']) for t in transactions]:
            month_key = f"{date.year}-{date.month:02d}"
            analysis['monthly_trends'][month_key]['total_spend'] += processed['current_amount']
            analysis['monthly_trends'][month_key]['subscription_count'] += 1

    # Process user-based statistics
    cutoff = datetime.now() - timedelta(days=180)
    for user_id, user_subs in grouped_user.items():
        user_data = {
            'user_id': user_id,
            'total_subscriptions': 0,
            'active_subscriptions': 0,
            'total_monthly_cost': defaultdict(float),
            'average_monthly_change': 0,
            'max_increase': {'subscription': '', 'increase': 0},
            'max_decrease': {'subscription': '', 'decrease': 0},
            'subscriptions': {}
        }
        all_changes = []

        for counterparty, transactions in user_subs.items():
            processed = process_subscription_transactions(transactions)
            if not processed:
                continue
            
            user_data['subscriptions'][counterparty] = processed
            user_data['total_subscriptions'] += 1
            user_data['total_monthly_cost'][processed['currency']] += processed['current_amount']
            
            # Check if active
            latest_date = parse_iso_datetime(transactions[-1]['updated_timestamp'])
            if latest_date > cutoff:
                user_data['active_subscriptions'] += 1
            
            # Track percentage changes
            all_changes.extend(processed['percentage_changes'])
            
            # Determine max increase/decrease
            if processed['percentage_changes']:
                current_max = max(processed['percentage_changes'])
                if current_max > user_data['max_increase']['increase']:
                    user_data['max_increase'] = {'subscription': counterparty, 'increase': current_max}
                
                current_min = min(processed['percentage_changes'])
                if current_min < user_data['max_decrease']['decrease']:
                    user_data['max_decrease'] = {'subscription': counterparty, 'decrease': current_min}

        # Calculate average change
        user_data['average_monthly_change'] = round(statistics.mean(all_changes), 2) if all_changes else 0
        user_data['total_monthly_cost'] = dict(user_data['total_monthly_cost'])
        analysis['user_stats'][user_id] = user_data

    # Calculate overall statistics
    all_changes = []
    for sub, stats in analysis['subscription_stats'].items():
        all_changes.extend(stats['percentage_changes'])
        if stats['percentage_changes']:
            max_change = max(stats['percentage_changes'])
            min_change = min(stats['percentage_changes'])
            if max_change > analysis['overall_stats']['top_increased']['increase']:
                analysis['overall_stats']['top_increased'] = {'name': sub, 'increase': max_change}
            if min_change < analysis['overall_stats']['top_decreased']['decrease']:
                analysis['overall_stats']['top_decreased'] = {'name': sub, 'decrease': min_change}
    
    if all_changes:
        analysis['overall_stats']['average_monthly_change'] = round(statistics.mean(all_changes), 2)
        analysis['overall_stats']['most_volatile'] = {
            'name': max(analysis['subscription_stats'], key=lambda k: max(map(abs, analysis['subscription_stats'][k]['percentage_changes']))),
            'change': round(max(map(abs, all_changes)), 2)
        }

    # Calculate active subscriptions (counterparty-based)
    analysis['active_subscriptions'] = sum(
        1 for transactions in grouped_counterparty.values() 
        if parse_iso_datetime(transactions[-1]['updated_timestamp']) > cutoff
    )

    return analysis

def generate_report(analysis):
    """Generate report with user breakdown"""
    report = {
        'metadata': {
            'total_subscriptions': analysis['total_subscriptions'],
            'active_subscriptions': analysis['active_subscriptions'],
            'analysis_date': datetime.now().isoformat()
        },
        'trend_analysis': analysis['overall_stats'],
        'monthly_breakdown': dict(analysis['monthly_trends']),
        'subscription_details': dict(analysis['subscription_stats']),
        'user_breakdown': {uid: dict(data) for uid, data in analysis['user_stats'].items()}
    }
    
    # Format numeric values
    for sub in report['subscription_details'].values():
        sub['percentage_changes'] = [round(c, 2) for c in sub['percentage_changes']]
    
    for user in report['user_breakdown'].values():
        user['average_monthly_change'] = round(user['average_monthly_change'], 2)
        user['max_increase']['increase'] = round(user['max_increase']['increase'], 2)
        user['max_decrease']['decrease'] = round(user['max_decrease']['decrease'], 2)
        for sub in user['subscriptions'].values():
            sub['percentage_changes'] = [round(c, 2) for c in sub['percentage_changes']]
    
    return report

def main():
    with open('synthetic_transactions.json', 'r') as f:
        transactions = json.load(f)
    
    analysis = analyze_subscriptions(transactions)
    report = generate_report(analysis)
    
    with open('subscription_analysis.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)

if __name__ == '__main__':
    main()