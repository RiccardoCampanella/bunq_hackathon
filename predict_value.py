import json
import pandas as pd
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

def parse_datetime(dt):
    """Universal datetime parser handling multiple formats"""
    if isinstance(dt, str):
        try:
            return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            try:
                return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                return datetime.now()  # Fallback for invalid dates
    return dt

def prepare_data(transactions):
    """Prepare training data with robust error handling"""
    df = pd.DataFrame(transactions)
    
    # Clean and filter data
    df = df[df['category'].isin(['RENT_AND_UTILITIES', 'SUBSCRIPTIONS', 'SALARY'])]
    df = df.dropna(subset=['category', 'amount'])
    
    # Convert data types
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df['updated_timestamp'] = df['updated_timestamp'].apply(parse_datetime)
    
    # Remove invalid entries
    df = df[df['amount'] > 0]
    df = df.sort_values('updated_timestamp')

    features = []
    targets = []
    
    grouped = df.groupby(['owner_user_id', 'category'])
    for (user_id, category), group in grouped:
        if len(group) < 2:
            continue  # Need at least 2 transactions to create features
            
        group = group.sort_values('updated_timestamp')
        for i in range(1, len(group)):
            try:
                current = group.iloc[i]
                previous = group.iloc[i-1]
                
                time_diff = (current['updated_timestamp'] - previous['updated_timestamp']).days
                amount_diff = current['amount'] - previous['amount']
                month = current['updated_timestamp'].month
                
                features.append({
                    'category': category,
                    'previous_amount': previous['amount'],
                    'days_since_last': time_diff,
                    'month': month,
                    'previous_change': amount_diff / previous['amount']
                })
                targets.append(1 if amount_diff > 0 else 0)
            except (KeyError, IndexError, ZeroDivisionError):
                continue
    
    return pd.DataFrame(features), pd.Series(targets)

def train_model(X, y):
    """Train model with proper category handling"""
    preprocessor = ColumnTransformer([
        ('cat', OneHotEncoder(handle_unknown='ignore'), ['category']),
        ('num', StandardScaler(), ['previous_amount', 'days_since_last', 'previous_change'])
    ])
    
    model = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', LogisticRegression(class_weight='balanced', max_iter=1000))
    ])
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Generate structured report
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    
    print("Model Evaluation:")
    print(classification_report(y_test, y_pred))
    
    return model, report

def predict_future(model, historical_data):
    """Safe prediction generation with validation"""
    predictions = []
    
    # Clean prediction data
    hist_df = historical_data.copy()
    hist_df['category'] = hist_df['category'].fillna('UNKNOWN')
    hist_df = hist_df[hist_df['category'].isin(['RENT_AND_UTILITIES', 'SUBSCRIPTIONS', 'SALARY'])]
    
    grouped = hist_df.groupby(['owner_user_id', 'category'])
    for (user_id, category), group in grouped:
        group = group.sort_values('updated_timestamp')
        if group.empty:
            continue
            
        latest = group.iloc[-1]
        try:
            days_since_last = (datetime.now() - latest['updated_timestamp']).days
            features = pd.DataFrame([{
                'category': category,
                'previous_amount': latest['amount'],
                'days_since_last': days_since_last,
                'month': datetime.now().month,
                'previous_change': 0
            }])
            
            pred = model.predict_proba(features)[0][1]
            predictions.append({
                'user_id': user_id,
                'category': category,
                'predicted_increase_probability': round(pred, 3)
            })
        except KeyError:
            continue
    
    return predictions

# Execution flow
with open('synthetic_transactions.json') as f:
    transactions = json.load(f)

# Prepare data
X, y = prepare_data(transactions)

# Handle case with insufficient data
if not X.empty and len(y.unique()) > 1:
    model, metrics = train_model(X, y)
    
    # Save model metrics
    with open('model_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=4)
    
    # Prepare prediction data
    raw_df = pd.DataFrame(transactions)
    raw_df['updated_timestamp'] = raw_df['updated_timestamp'].apply(parse_datetime)
    latest_transactions = raw_df.sort_values('updated_timestamp').groupby(['owner_user_id', 'category']).last().reset_index()
    
    # Generate and save predictions
    predictions = predict_future(model, latest_transactions)
    print("\nPredicted Increase Probabilities:")
    print(pd.DataFrame(predictions))
    
    with open('regression_values.json', 'w') as f:
        json.dump(predictions, f, indent=4)
else:
    print("Insufficient data for training. Need more historical transactions.")