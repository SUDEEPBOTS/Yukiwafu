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

# Yahan maine standard rarities aur teri DB wali rarities merge kar di hain
RARITY_WEIGHTS = {
    "⚪️ Common": (40, True),
    "🟢 Uncommon": (30, True),
    "🔵 Rare": (20, True),
    "🟣 Epic": (10, True),
    "🟡 Legendary": (5, True),
    "👑 Mythical": (2, True),
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

    # Fetch characters from MongoDB based on allowed rarities
    allowed_rarities = [k for k, v in RARITY_WEIGHTS.items() if v[1]]
    all_characters = list(await collection.find({"rarity": {"$in": allowed_rarities}}).to_list(length=None))

    # 🔥 THE MASTER FALLBACK: Agar allowed rarities na milein, toh poore database se utha lo!
    if not all_characters:
        all_characters = list(await collection.find({}).to_list(length=None))
        
    if not all_characters:
        await context.bot.send_message(chat_id, "Bhai, database ekdum khaali hai! Ek bhi Waifu nahi mili.")
        return

    # Filter characters
    available_characters = [
        c for c in all_characters 
        if 'id' in c and c.get('rarity') is not None
    ]

    # Agar ab bhi filter hone ke baad empty ho (jo ki nahi hoga), toh sabko allowed maan lo
    if not available_characters:
        available_characters = all_characters

    # Weighted random selection
    cumulative_weights = []
    cumulative_weight = 0
    for char in available_characters:
        # Agar koi nayi rarity aati hai jo list mein nahi hai, toh default weight 1 milega
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

    # Naya character save ho raha hai
    last_characters[chat_id] = selected_character
    last_characters[chat_id]['timestamp'] = time.time()
    
    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    rarity_text = selected_character.get('rarity', 'Unknown Rarity')
    caption_text = f"✨ A {rarity_text} Character Appears! ✨\n🔍 Use /guess to claim this mysterious character!\n💫 Hurry, before someone else snatches them!"

    # 🔥 THE HACKER FIX: Tute hue link se bachne ka tareeqa
    fallback_img = "https://files.catbox.moe/7ccoub.jpg" # Agar DB wala link fail ho jaye
    img_to_send = selected_character.get('img_url', fallback_img)

    try:
        # Spoiler effect ke sath image/video send karo
        if 'vid_url' in selected_character:
            sent_message = await context.bot.send_video(
                chat_id=chat_id,
                video=selected_character['vid_url'],
                caption=caption_text,
                parse_mode='Markdown',
                has_spoiler=True
            )
        else:
            sent_message = await context.bot.send_photo(
                chat_id=chat_id,
                photo=img_to_send,
                caption=caption_text,
                parse_mode='Markdown',
                has_spoiler=True
            )

        # Schedule message deletion after 5 minutes
        asyncio.create_task(delete_message(chat_id, sent_message.message_id, context))
        
    except Exception as e:
        print(f"⚠️ Link toot gaya ya Telegram nakhre kar raha hai (Waifu ID {selected_character.get('id')}): {e}")
        try:
            # Plan B: Chupchaap default photo chipka do, game mat rukne do!
            sent_message = await context.bot.send_photo(
                chat_id=chat_id,
                photo=fallback_img,
                caption=f"⚠️ {rarity_text} Waifu ka photo link toot gaya tha, par guessing jaari hai!\n🔍 /guess karo!",
                parse_mode='Markdown'
            )
            asyncio.create_task(delete_message(chat_id, sent_message.message_id, context))
        except Exception as deep_e:
            print(f"❌ Plan B bhi fail ho gaya: {deep_e}")
            
