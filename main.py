# main.py
import os
from numpy import random
from financial_meme_generator.data_loader import load_json_data, inspect_json
from financial_meme_generator.transaction_analysis import (
    get_matching_keys, get_owner_user_id, get_transactions_for_user,
    match_transactions, get_earliest_latest_transactions,
    sort_transactions_by_timestamp, get_account_balance,
    get_last_transaction_before_account_balance
)
from financial_meme_generator.caption_generator import (
    initialize_openai_client, generate_caption, generate_image_description
)
from financial_meme_generator.image_utils import (
    fetch_image_url, show_image_from_url, generate_meme
)

def main():
    # Define paths and files
    base_path_jsons = r'C:\Users\sliktjg\OneDrive - TNO\Documents\Hackathon\data'
    json_files = [
        'activities.json',
        'cards.json',
        'deeplinks.json',
        'monetary_accounts.json',
        'together_topics.json',
        'transactions.json'
    ]
    
    # Load and analyze data
    json_data = load_json_data(base_path_jsons, json_files)
    inspect_json(json_data)
    
    # Get transaction data
    matching_keys = get_matching_keys(json_data['monetary_accounts.json'], json_data['transactions.json'])
    print(f'Matching keys between monetary_accounts and transactions: {matching_keys}')
    
    owner_user_ids = get_owner_user_id(json_data['monetary_accounts.json'])
    print(f'Owner user IDs in monetary_accounts: {owner_user_ids}')
    
    # Process transactions for each user
    transactions_per_user = {
        user_id: get_transactions_for_user(json_data['transactions.json'], user_id)
        for user_id in owner_user_ids
    }
    
    # Generate meme from random transaction
    sorted_transactions = sort_transactions_by_timestamp(transactions_per_user)
    
    # Initialize API client
    client = initialize_openai_client(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key="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"
    )
    user_id = '771'
    event_id = "452"
    # Select random transaction and generate meme
    if user_id in sorted_transactions and sorted_transactions['771']:
        rand_choice = random.randint(0, len(sorted_transactions['771']))

        for transaction in sorted_transactions['771']:
            if transaction['event_id'] == event_id:
                print(f"Transaction: {transaction}")
                break

        transaction = sorted_transactions[user_id][rand_choice]
        print(f"Transaction: {transaction}")

        caption = generate_caption(client, transaction)
        print(f"Caption: {caption}")
        
        image_description = generate_image_description(client, caption)
        print(f"Image description: {image_description}")
        
        url = fetch_image_url(image_description)
        if url:
            print(f"Image URL: {url}")
            show_image_from_url(url)
            print(f"Generating meme with caption: {caption}")
            meme = generate_meme(url, caption, "meme.jpg")
        else:
            print(f"No valid image URL found for '{image_description}'.")

if __name__ == "__main__":
    main()
