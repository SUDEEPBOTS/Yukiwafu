from TEAMZYRO import *
import random
import asyncio
import time
from telegram import Update
from telegram.ext import CallbackContext

log = "-1003745635449"

async def delete_message(chat_id, message_id, context):
    await asyncio.sleep(300)  # 5 minutes (300 seconds)
    try:
        await context.bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")

RARITY_WEIGHTS = {
    "⚪️ Low": (40, True),              
    "🟠 Medium": (20, True),           
    "🔴 High": (12, True),             
    "🎩 Special Edition": (8, True),   
    "🪽 Elite Edition": (6, True),     
    "🪐 Exclusive": (4, True),         
    "💞 Valentine": (2, False),         
    "🎃 Halloween": (2, False),        
    "❄️ Winter": (1.5, False),          
    "🏖 Summer": (1.2, False),          
    "🎗 Royal": (0.5, False),           
    "💸 Luxury Edition": (0.5, False)   
}

async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    # Fetch all characters from MongoDB
    allowed_rarities = [k for k, v in RARITY_WEIGHTS.items() if v[1]]
    all_characters = list(await collection.find({"rarity": {"$in": allowed_rarities}}).to_list(length=None))

    if not all_characters:
        await context.bot.send_message(chat_id, "No characters found with allowed rarities in the database.")
        return

    # Filter characters with valid rarity
    available_characters = [
        c for c in all_characters 
        if 'id' in c and c.get('rarity') is not None and RARITY_WEIGHTS.get(c.get('rarity'), (0, False))[1]
    ]

    if not available_characters:
        await context.bot.send_message(chat_id, "No available characters with the allowed rarities.")
        return

    # Weighted random selection
    cumulative_weights = []
    cumulative_weight = 0
    for char in available_characters:
        cumulative_weight += RARITY_WEIGHTS.get(char.get('rarity'), (1, False))[0]
        cumulative_weights.append(cumulative_weight)

    rand = random.uniform(0, cumulative_weight)
    selected_character = None
    for i, char in enumerate(available_characters):
        if rand <= cumulative_weights[i]:
            selected_character = char
            break

    if not selected_character:
        selected_character = random.choice(available_characters)

    # FIX: Pehle 'character' save ho raha tha jo loop ka aakhri item tha. 
    # Ab 'selected_character' save hoga.
    last_characters[chat_id] = selected_character
    last_characters[chat_id]['timestamp'] = time.time()
    
    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    rarity_text = selected_character.get('rarity', 'Unknown Rarity')
    caption_text = f"A {rarity_text} Character Appears!\nUse /guess to claim this mysterious character!\nHurry, before someone else snatches them!"

    # Check if the character has a video URL
    if 'vid_url' in selected_character:
        sent_message = await context.bot.send_video(
            chat_id=chat_id,
            video=selected_character['vid_url'],
            caption=caption_text,
            parse_mode='Markdown',
            has_spoiler=True  # Spoiler effect for video
        )
    else:
        sent_message = await context.bot.send_photo(
            chat_id=chat_id,
            photo=selected_character.get('img_url', ''),
            caption=caption_text,
            parse_mode='Markdown',
            has_spoiler=True  # Spoiler effect for image
        )

    # Schedule message deletion after 5 minutes
    asyncio.create_task(delete_message(chat_id, sent_message.message_id, context))
    
