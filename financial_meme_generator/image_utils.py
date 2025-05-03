# financial_meme_generator/image_utils.py
from duckduckgo_search import DDGS
import requests
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image, ImageDraw, ImageFont
import textwrap

def fetch_image_url(query):
    """Search for and retrieve an image URL based on query."""
    with DDGS() as ddgs:
        results = ddgs.images(query, max_results=1)
        for result in results:
            image_url = result.get("image")
            if image_url:
                return image_url
    return None

def show_image_from_url(img_url):
    """Display an image from URL using matplotlib."""
    try:
        response = requests.get(img_url)
        img = mpimg.imread(BytesIO(response.content), format='jpg')
        # plt.imshow(img)
        # plt.axis('off')
        # plt.show()
        return img
    except Exception as e:
        print(f"Failed to load image: {e}")
        return None

def generate_meme(image_url, caption, output_path="meme.jpg"):
    """Generate a meme with caption from an image URL."""
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content)).convert("RGB")
    img = img.resize((500, 500))  # Resize to a standard size
    font_size = 30  # Default font size

    draw = ImageDraw.Draw(img)
    
    # Calculate target width (90% of image width)
    target_width = int(img.width * 0.9)
    
    # Split caption into top and bottom parts
    caption_parts = caption.split()
    mid_point = len(caption_parts) // 2
    top_caption = " ".join(caption_parts[:mid_point]).upper()
    bottom_caption = " ".join(caption_parts[mid_point:]).upper()

    # Find appropriate font size that makes text width close to target_width
    max_font_size = int(img.height)
    min_font_size = 20
    
    # Function to get the best font size
    def get_best_font_size(text, target_width):
        current_size = min_font_size
        
        while current_size <= max_font_size:
            try:
                test_font = ImageFont.truetype("Impact.ttf", current_size)
            except:
                test_font = ImageFont.load_default()
                
            text_bbox = draw.textbbox((0, 0), text, font=test_font)
            text_width = text_bbox[2] - text_bbox[0]
            
            if text_width > target_width:
                return max(current_size - 1, min_font_size)
            
            current_size += 1
        
        return min(current_size - 1, max_font_size)
    
        # Calculate appropriate characters per line based on image width
    chars_per_line = int(target_width / (font_size * 0.6))  # Estimate characters that fit in target width
    
    # Wrap text to fit target width
    top_wrapped = textwrap.fill(top_caption, width=chars_per_line)
    bottom_wrapped = textwrap.fill(bottom_caption, width=chars_per_line)
    
    # Get the longest line from each wrapped text to determine font size
    top_longest = max(top_wrapped.split('\n'), key=len) if top_wrapped else ""
    bottom_longest = max(bottom_wrapped.split('\n'), key=len) if bottom_wrapped else ""
    
    # Determine font size based on the longer of the two captions
    if len(top_longest) >= len(bottom_longest):
        font_size = get_best_font_size(top_longest, target_width)
    else:
        font_size = get_best_font_size(bottom_longest, target_width)
    
    # Load font with calculated size
    try:
        font = ImageFont.truetype("Impact.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Re-wrap text with the final font size for better accuracy
    chars_per_line = int(target_width)
    top_wrapped = textwrap.fill(top_caption, width=chars_per_line)
    bottom_wrapped = textwrap.fill(bottom_caption, width=chars_per_line)

    # Calculate text positions
    top_bbox = draw.textbbox((0, 0), top_wrapped, font=font)
    top_text_width = top_bbox[2] - top_bbox[0]
    top_text_height = top_bbox[3] - top_bbox[1]
    
    bottom_bbox = draw.textbbox((0, 0), bottom_wrapped, font=font)
    bottom_text_width = bottom_bbox[2] - bottom_bbox[0]
    bottom_text_height = bottom_bbox[3] - bottom_bbox[1]
    
    top_x = (img.width - top_text_width) / 2
    top_y = 10  # Top caption
    
    bottom_x = (img.width - bottom_text_width) / 2
    bottom_y = img.height - bottom_text_height - 10  # Bottom caption

    # Draw top caption (outline + text)
    for dx in [-2, -1, 0, 1, 2]:
        for dy in [-2, -1, 0, 1, 2]:
            draw.text((top_x + dx, top_y + dy), top_wrapped, font=font, fill="black")
    draw.text((top_x, top_y), top_wrapped, font=font, fill="white")

    # Draw bottom caption (outline + text)
    for dx in [-2, -1, 0, 1, 2]:
        for dy in [-2, -1, 0, 1, 2]:
            draw.text((bottom_x + dx, bottom_y + dy), bottom_wrapped, font=font, fill="black")
    draw.text((bottom_x, bottom_y), bottom_wrapped, font=font, fill="white")

    img.save(output_path)
    # plot the image
    img_to_show = mpimg.imread(output_path)
    plt.imshow(img_to_show)
    plt.axis('off')
    plt.show()
    return img

