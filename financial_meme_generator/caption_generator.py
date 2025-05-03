# financial_meme_generator/caption_generator.py
from openai import OpenAI

def initialize_openai_client(base_url, api_key):
    """Initialize OpenAI client with provided credentials."""
    return OpenAI(
        base_url=base_url,
        api_key=api_key
    )

def generate_caption(client, transaction):
    """Generate a caption for a financial transaction."""
    description = transaction['transaction_description']
    amount = transaction['amount']
    transaction_type = transaction['transaction_type']
    transaction_date = transaction['updated_timestamp']
    
    caption_prompt = f"You are a financial meme caption generator. Generate a caption to the situation where you spent {amount} on {description} ({transaction_type}) on {transaction_date}. The caption should be funny and relatable. The caption should be in English. The caption should be short and to the point. The caption should be a single sentence. The caption should not contain any hashtags or emojis. Direct the caption at the owner of the bank account from the transaction."
    
    caption_response = client.chat.completions.create(
        model="nvidia/llama-3.1-nemotron-70b-instruct",
        messages=[
            {"role": "system", "content": "You are a financial meme caption generator. You generate captions for financial memes. The captions should be in English. The captions should be short and to the point. The captions should be a single sentence. The captions should not contain any hashtags or emojis. Make it funny, sarcastic, motivational, frustrated or relatable based on the situation."},
            {"role": "user", "content": caption_prompt}
        ],
        temperature=0.7,
        top_p=1,
        max_tokens=100
    )
    
    return caption_response.choices[0].message.content

def generate_image_description(client, caption):
    """Generate a short image description based on caption."""
    image_prompt = f"Creatively summarize '{caption}' in three words."
    
    image_response = client.chat.completions.create(
        model="nvidia/llama-3.1-nemotron-70b-instruct",
        messages=[
            {"role": "system", "content": "You are a image description generator. You generate descriptions for images. The descriptions should be short and to the point. Maximum 3 words. The descriptions should be a single sentence. The descriptions should not contain any hashtags or emojis."},
            {"role": "user", "content": image_prompt}
        ],
        temperature=0.5,
        top_p=1,
        max_tokens=50
    )
    
    return image_response.choices[0].message.content
