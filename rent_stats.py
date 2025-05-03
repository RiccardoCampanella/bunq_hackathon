import json
import re
import statistics
from collections import defaultdict
from datetime import datetime
from geopy.distance import great_circle

# Configuration
DATA_FILES = {
    'transactions': 'synthetic_transactions.json',
    'activities': 'activities.json',
    'accounts': 'monetary_accounts.json',
    'cards': 'cards.json'
}

OUTPUT_FILE = 'rental_analysis_report.json'
VALID_RENT_RANGE = (300, 10000)
COUNTRY_MAPPING = {
    'USA': 'US', 'GB': 'UK', '': 'UNKNOWN',
    'BELGIUM': 'BE', 'NL': 'NL', 'HOLLAND': 'NL',
    'THE NETHERLANDS': 'NL', 'NETHERLANDS': 'NL',
    'DE': 'DE', 'FR': 'FR', 'CH': 'CH', 'UN': 'UNKNOWN'
}

DUTCH_CITIES = {
    'amsterdam', 'rotterdam', 'the hague', 'utrecht', 'eindhoven',
    'tilburg', 'groningen', 'almere', 'breda', 'nijmegen', 'hilversum'
}

def parse_rental_place(rental_place):
    """Extract city and country from Rental_Place field"""
    if not rental_place:
        return {'city': '', 'country': 'UNKNOWN'}
    
    patterns = [
        r'(?P<city>[A-Z][a-z]+(?: [A-Za-z]+)*)\s*[,;]\s*(?P<country>[A-Z]{2})\b',
        r'\b(?P<country>[A-Z]{2})\s*-\s*(?P<city>[A-Z][a-z]+(?: [A-Za-z]+)*)',
        r'(?P<city>[A-Z][a-z]+(?: [A-Za-z]+)*)\s+\((?P<country>[A-Z]{2})\)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, rental_place)
        if match:
            country = COUNTRY_MAPPING.get(match.group('country').upper(), 'UNKNOWN')
            return {
                'city': match.group('city').strip().title(),
                'country': country
            }
    
    parts = [p.strip() for p in rental_place.split(',')]
    if len(parts) >= 2:
        country = COUNTRY_MAPPING.get(parts[-1].upper(), 'UNKNOWN')
        return {'city': parts[0].title(), 'country': country}
    
    return {'city': rental_place.title(), 'country': 'UNKNOWN'}

def extract_city_from_address(address):
    """Extract city from address field"""
    parts = [p.strip() for p in address.split(',') if p.strip()]
    if len(parts) > 1 and not re.match(r'^\d+', parts[-1]):
        return parts[-2].title()
    return ''

def extract_city_from_text(text):
    """Extract city names from free-form text fields"""
    if not text:
        return ''
    
    text_lower = text.lower()
    for city in DUTCH_CITIES:
        if city in text_lower:
            return city.title()

    patterns = [
        r'\b(?:in|at|near|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:city|town)\b',
        r'\b\d{4}\s?[A-Za-z]{2}\s+([A-Z][a-z]+)\b'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, flags=re.IGNORECASE)
        for match in matches:
            city = match.group(1).strip()
            city = re.sub(r'[\d\-\.\(\)]', '', city).strip()
            if 2 <= len(city.split()) <= 3:
                return city.title()
    
    return ''

def enhance_transaction_data(transaction):
    """Enhance transaction with location data"""
    rental_info = parse_rental_place(transaction.get('Rental_Place', ''))
    transaction['city'] = rental_info['city']
    transaction['country'] = rental_info['country']
    
    if not transaction['city']:
        transaction['city'] = extract_city_from_address(
            transaction.get('place_address', '')
        )
    
    if not transaction['city']:
        transaction['city'] = extract_city_from_text(
            transaction.get('transaction_description', '')
        )
    
    transaction['country'] = COUNTRY_MAPPING.get(
        transaction['country'].upper(), 
        transaction['country']
    )[:2]
    
    if transaction['city'].lower() in DUTCH_CITIES:
        transaction['country'] = 'NL'
    
    return transaction

def load_and_clean_data(file_key):
    """Load and preprocess data"""
    try:
        with open(DATA_FILES[file_key], 'r') as f:
            data = json.load(f)
            
        if file_key == 'transactions':
            for item in data:
                enhance_transaction_data(item)
        return data
    except Exception as e:
        print(f"Error loading {file_key}: {e}")
        raise

def calculate_geographical_stats(locations):
    """Calculate geographical metrics"""
    if not locations:
        return None
    
    valid_locs = []
    for loc in locations:
        try:
            lat = round(float(loc[0]), 6)
            lon = round(float(loc[1]), 6)
            valid_locs.append((lat, lon))
        except (TypeError, ValueError):
            continue
    
    if not valid_locs:
        return None
    
    lats = [loc[0] for loc in valid_locs]
    lons = [loc[1] for loc in valid_locs]
    
    center = (
        round(statistics.mean(lats), 6),
        round(statistics.mean(lons), 6)
    )
    
    max_distance = 0
    for i in range(len(valid_locs)):
        for j in range(i+1, len(valid_locs)):
            distance = great_circle(valid_locs[i], valid_locs[j]).km
            max_distance = max(max_distance, round(distance, 2))
    
    return {
        'geographical_center': center,
        'spread_km': max_distance,
        'location_clusters': valid_locs
    }

def analyze_data(transactions):
    """Perform comprehensive analysis using owner_user_id"""
    analysis = {
        'financial': defaultdict(lambda: {
            'total_transactions': 0,
            'total_amount': 0.0,
            'amounts': [],
            'country_distribution': defaultdict(int)
        }),
        'geography': defaultdict(lambda: {
            'transaction_count': 0,
            'total_amount': 0.0,
            'city_distribution': defaultdict(int),
            'location_clusters': []
        }),
        'users': defaultdict(lambda: {
            'total_transactions': 0,
            'total_amount': 0.0,
            'amounts': [],
            'country_distribution': defaultdict(int),
            'city_distribution': defaultdict(int),
            'location_clusters': []
        }),
        'metadata': {
            'total_transactions_analyzed': len(transactions),
            'analysis_date': datetime.now().isoformat(),
            'data_sources': DATA_FILES
        }
    }

    for tx in transactions:
        user_type = tx.get('user_type', 'null')
        user_id = tx.get('owner_user_id', 'unknown')  # Updated field
        amount = abs(float(tx.get('amount', 0)))
        country = tx.get('country', 'UNKNOWN')
        city = tx.get('city', 'Unknown')

        # Financial analysis by user type
        financial = analysis['financial'][user_type]
        financial['total_transactions'] += 1
        financial['total_amount'] += amount
        financial['amounts'].append(amount)
        financial['country_distribution'][country] += 1

        # Geographical analysis
        geo = analysis['geography'][country]
        geo['transaction_count'] += 1
        geo['total_amount'] += amount
        geo['city_distribution'][city] += 1

        # User analysis using owner_user_id
        user_data = analysis['users'][user_id]
        user_data['total_transactions'] += 1
        user_data['total_amount'] += amount
        user_data['amounts'].append(amount)
        user_data['country_distribution'][country] += 1
        user_data['city_distribution'][city] += 1

        # Geolocation processing
        try:
            lat = tx.get('geolocation_latitude')
            lon = tx.get('geolocation_longitude')
            if lat and lon:
                geo_loc = (float(lat), float(lon))
                geo['location_clusters'].append(geo_loc)
                user_data['location_clusters'].append(geo_loc)
        except (TypeError, ValueError):
            pass

    # Calculate financial stats
    for user_type, data in analysis['financial'].items():
        amounts = data['amounts']
        if amounts:
            data['average_amount'] = round(statistics.mean(amounts), 2)
            data['median_amount'] = round(statistics.median(amounts), 2)
            data['min_amount'] = round(min(amounts), 2)
            data['max_amount'] = round(max(amounts), 2)
            data['std_deviation'] = round(statistics.stdev(amounts), 2) if len(amounts) > 1 else 0.0
        else:
            data.update({
                'average_amount': 0.0,
                'median_amount': 0.0,
                'min_amount': 0.0,
                'max_amount': 0.0,
                'std_deviation': 0.0
            })
        data['top_country'] = max(
            data['country_distribution'].items(),
            key=lambda x: x[1],
            default=('', 0)
        )
        del data['amounts']

    # Calculate user stats
    for user_id, user_data in analysis['users'].items():
        amounts = user_data['amounts']
        if amounts:
            user_data['average_amount'] = round(statistics.mean(amounts), 2)
            user_data['median_amount'] = round(statistics.median(amounts), 2)
            user_data['min_amount'] = round(min(amounts), 2)
            user_data['max_amount'] = round(max(amounts), 2)
            user_data['std_deviation'] = round(statistics.stdev(amounts), 2) if len(amounts) > 1 else 0.0
        else:
            user_data.update({
                'average_amount': 0.0,
                'median_amount': 0.0,
                'min_amount': 0.0,
                'max_amount': 0.0,
                'std_deviation': 0.0
            })
        
        user_data['top_country'] = max(
            user_data['country_distribution'].items(),
            key=lambda x: x[1],
            default=('', 0)
        )
        user_data['top_city'] = max(
            user_data['city_distribution'].items(),
            key=lambda x: x[1],
            default=('', 0)
        )
        
        geo_stats = calculate_geographical_stats(user_data['location_clusters'])
        if geo_stats:
            user_data['geographical_center'] = geo_stats['geographical_center']
            user_data['spread_km'] = geo_stats['spread_km']
        else:
            user_data['geographical_center'] = None
            user_data['spread_km'] = 0.0
        del user_data['location_clusters']

    # Calculate geography stats
    for country, data in analysis['geography'].items():
        geo_stats = calculate_geographical_stats(data['location_clusters'])
        if geo_stats:
            data.update(geo_stats)
        del data['location_clusters']

    return analysis

def generate_report(analysis):
    """Generate final report with user analysis"""
    report = {
        'metadata': analysis['metadata'],
        'financial_analysis': {},
        'geographical_insights': {
            'country_analysis': {},
            'match_breakdown': {
                'coordinates': sum(1 for c in analysis['geography'].values() if c.get('geographical_center')),
                'place_name': analysis['metadata']['total_transactions_analyzed'] - sum(1 for c in analysis['geography'].values() if c.get('geographical_center'))
            }
        },
        'user_analysis': {}
    }

    # Financial analysis
    for user_type, data in analysis['financial'].items():
        report['financial_analysis'][user_type] = {
            'total_transactions': data['total_transactions'],
            'total_amount': round(data['total_amount'], 2),
            'average_amount': data['average_amount'],
            'median_amount': data['median_amount'],
            'min_amount': data['min_amount'],
            'max_amount': data['max_amount'],
            'std_deviation': data['std_deviation'],
            'country_distribution': dict(data['country_distribution']),
            'top_country': list(data['top_country'])
        }

    # Geographical insights
    for country, data in analysis['geography'].items():
        report['geographical_insights']['country_analysis'][country] = {
            'transaction_count': data['transaction_count'],
            'total_amount': round(data['total_amount'], 2),
            'city_distribution': dict(data['city_distribution']),
            'geographical_center': data.get('geographical_center'),
            'spread_km': data.get('spread_km', 0.0)
        }

    # User analysis
    for user_id, data in analysis['users'].items():
        report['user_analysis'][user_id] = {
            'total_transactions': data['total_transactions'],
            'total_amount': round(data['total_amount'], 2),
            'average_amount': data['average_amount'],
            'median_amount': data['median_amount'],
            'min_amount': data['min_amount'],
            'max_amount': data['max_amount'],
            'std_deviation': data['std_deviation'],
            'country_distribution': dict(data['country_distribution']),
            'city_distribution': dict(data['city_distribution']),
            'top_country': list(data['top_country']),
            'top_city': list(data['top_city']),
            'geographical_center': data.get('geographical_center'),
            'spread_km': data.get('spread_km', 0.0)
        }

    return report

def main():
    print("Starting rental market analysis...")
    
    transactions = load_and_clean_data('transactions')
    
    rent_transactions = [
        tx for tx in transactions
        if tx.get('category') == 'RENT_AND_UTILITIES'
        and VALID_RENT_RANGE[0] <= abs(float(tx.get('amount', 0))) <= VALID_RENT_RANGE[1]
    ]
    
    analysis = analyze_data(rent_transactions)
    report = generate_report(analysis)
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Analysis complete. Results saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()