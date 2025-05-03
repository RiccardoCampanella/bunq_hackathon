# financial_meme_generator/transaction_analysis.py

def get_matching_keys(monetary_accounts, transactions):
    """Get matching keys between monetary accounts and transactions."""
    matching_keys = set(monetary_accounts[0].keys()).intersection(set(transactions[0].keys()))
    return matching_keys

def get_owner_user_id(monetary_accounts):
    """Extract owner user IDs from monetary accounts."""
    owner_user_ids = set()
    for account in monetary_accounts:
        if 'owner_user_id' in account:
            owner_user_ids.add(account['owner_user_id'])
    return owner_user_ids

def get_transactions_for_user(transactions, user_id):
    """Filter transactions by user ID."""
    user_transactions = []
    for transaction in transactions:
        if 'owner_user_id' in transaction and transaction['owner_user_id'] == user_id:
            user_transactions.append(transaction)
    return user_transactions

def match_transactions(transactions_per_user, monetary_accounts):
    """Match transactions between users based on IBAN."""
    from_to_transactions = {}
    for user_id, transactions in transactions_per_user.items():
        from_to_transactions[user_id] = []
        for transaction in transactions:
            if 'counterparty_iban' in transaction:
                for account in monetary_accounts:
                    if account.get('IBAN') == transaction['counterparty_iban']:
                        from_to_transactions[user_id].append(transaction['event_id'])
                        break
    return from_to_transactions

def get_earliest_latest_transactions(transactions):
    """Find earliest and latest transactions based on timestamp."""
    earliest_transaction = None
    latest_transaction = None
    for transaction in transactions:
        if earliest_transaction is None or transaction['updated_timestamp'] < earliest_transaction['updated_timestamp']:
            earliest_transaction = transaction
        if latest_transaction is None or transaction['updated_timestamp'] > latest_transaction['updated_timestamp']:
            latest_transaction = transaction
    return earliest_transaction, latest_transaction

def sort_transactions_by_timestamp(transactions_per_user):
    """Sort transactions chronologically by timestamp."""
    sorted_transactions_per_user = {}
    for user_id, transactions in transactions_per_user.items():
        sorted_transactions_per_user[user_id] = sorted(transactions, key=lambda x: x['updated_timestamp'])
    return sorted_transactions_per_user

def get_account_balance(monetary_accounts, user_id):
    """Get account balance and timestamp for a user."""
    for account in monetary_accounts:
        if account['owner_user_id'] == user_id:
            timestamp = account['updated_timestamp']
            print(f'User ID: {user_id}, Updated timestamp: {timestamp}')
            return account['AccountBalance'], timestamp
    return None, None

def get_last_transaction_before_account_balance(sorted_transactions, timestamp):
    """Find the last transaction before a given timestamp."""
    last_transaction = None
    for transaction in sorted_transactions:
        if transaction['updated_timestamp'] < timestamp:
            last_transaction = transaction
        else:
            break
    return last_transaction
