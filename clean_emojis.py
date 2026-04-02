import json
import re

def remove_emojis(text):
    """Remove all Unicode emoji characters and related characters from a string."""
    if text is None:
        return None

    # This regex pattern matches most emoji characters
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U0001F1F0-\U0001F1FF"  # more flags
        "\U00002500-\U00002BEF"  # chinese char
        "\U00002702-\U000027B0"
        "\U00002700-\U000027BF"  # Dingbats
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2600-\u26FF"
        "\u2700-\u27BF"
        "\u231A-\u231B"  # Watch
        "\u23E9-\u23EC"  # Black Right-Pointing Double Triangle
        "\u23F0"         # Alarm Clock
        "\u23F3"         # Hourglass Not Done
        "\u25AA-\u25AB"  # Square
        "\u25FB-\u25FE"  # White/Black Medium Squares
        "\u2605"         # Star
        "\u2614-\u2615"  # Umbrella/Umbrella With Rain Drops, Hot Beverage
        "\u2648-\u2653"  # Zodiac Signs
        "\u267F"         # Wheelchair Symbol
        "\u2693"         # Anchor
        "\u26A1"         # High Voltage
        "\u26AA-\u26AB"  # White/Black Circle
        "\u26BD-\u26BE"  # Soccer Ball/Circle With Left Half Black
        "\u26C4-\u26C5"  # Snowman/Sun Behind Cloud
        "\u26CE"         # Ophiuchus
        "\u26D4"         # No Entry
        "\u26EA"         # Church
        "\u26F2-\u26F3"  # Fountain/Flag In Hole
        "\u26F5"         # Sailboat
        "\u26FA"         # Tent
        "\u26FD"         # Fuel Pump
        "\u2705"         # White Heavy Check Mark
        "\u270A-\u270B"  # Raised Fist/Raised Hand
        "\u2728"         # Sparkles
        "\u274C"         # Cross Mark
        "\u274E"         # Negative Squared Cross Mark
        "\u2753-\u2755"  # Black Question Mark Ornament/White Question Mark Ornament/White Exclamation Mark Ornament
        "\u2757"         # Heavy Exclamation Mark Symbol
        "\u2795-\u2797"  # Heavy Plus Sign/Heavy Minus Sign/Heavy Division Sign
        "\u27B0"         # Curly Loop
        "\u27BF"         # Double Curly Loop
        "\u2B1B-\u2B1C"  # Black/White Large Square
        "\u2B50"         # White Medium Star
        "\u2B55"         # Heavy Large Circle
        "\u3030"         # Wavy Dash
        "\u303D"         # Part Alternation Mark
        "\u3297"         # Circled Ideograph Congratulation
        "\u3299"         # Circled Ideograph Secret
        "]+",
        flags=re.UNICODE
    )

    # Remove emoji characters
    cleaned_text = emoji_pattern.sub('', text)

    # Remove zero-width joiner characters that might be left over
    cleaned_text = cleaned_text.replace('\u200D', '')  # Zero-width joiner

    # Remove leading/trailing whitespace
    return cleaned_text.strip()

def clean_json_data(data):
    """Recursively clean JSON data by removing emojis from keys and string values."""
    if isinstance(data, dict):
        # Create a new dictionary with cleaned keys and values
        cleaned_dict = {}
        for key, value in data.items():
            # Clean the key
            cleaned_key = remove_emojis(key)
            # Clean the value
            cleaned_value = clean_json_data(value)
            cleaned_dict[cleaned_key] = cleaned_value
        return cleaned_dict
    elif isinstance(data, list):
        # Process each item in the list
        return [clean_json_data(item) for item in data]
    elif isinstance(data, str):
        # Clean string values
        return remove_emojis(data)
    else:
        # Return other data types unchanged
        return data

def main():
    # Load the JSON data
    with open('config-list-transformed.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Clean the data
    cleaned_data = clean_json_data(data)

    # Save the cleaned data
    with open('config-list-transformed-cleaned.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

    print("Emoji removal completed. Cleaned data saved to 'config-list-transformed-cleaned.json'")

if __name__ == "__main__":
    main()