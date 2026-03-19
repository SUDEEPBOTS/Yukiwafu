from TEAMZYRO import app, collection as character_collection, user_collection
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

import asyncio 

@app.on_message(filters.command("check"))
async def check_character(client, message):
    args = message.command
    if len(args) < 2:
        await message.reply_text("Bhai, ek Character ID toh de! Ex: `/check 01`")
        return

    character_id = args[1]
    character = await character_collection.find_one({'id': character_id})

    if not character:
        await message.reply_text("Ye character database mein nahi mila! ❌")
        return

    # Create the 'Who Have It' button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Who Have It?", callback_data=f"whohaveit_{character_id}")]
    ])

    # 🔥 FIX 1: KeyError se bachne ke liye '.get()' use kiya. 
    anime_name = character.get('anime', character.get('event_tag', 'N/A'))
    
    # 🔥 FIX 2: Baaki sab mein bhi '.get()' lagaya taaki future mein crash na ho
    text = (
        f"🌟 **Character Info**\n"
        f"🆔 ID: `{character.get('id', character_id)}`\n"
        f"📛 Name: {character.get('name', 'Unknown')}\n"
        f"📺 Anime/Event: {anime_name}\n"
        f"💎 Rarity: {character.get('rarity', 'Unknown')}\n"
    )

    # 🔥 THE HACKER FIX: Tute hue link se bachne ka tareeqa
    fallback_img = "https://files.catbox.moe/7ccoub.jpg" 

    try:
        if 'vid_url' in character:
            await message.reply_video(character['vid_url'], caption=text, reply_markup=keyboard)
        else:
            img_to_send = character.get('img_url', fallback_img)
            # Agar DB mein link empty string ("") ho toh bhi fallback use karega
            if not img_to_send:
                img_to_send = fallback_img
            await message.reply_photo(img_to_send, caption=text, reply_markup=keyboard)
            
    except Exception as e:
        print(f"⚠️ /check command pe link toot gaya (Waifu ID {character_id}): {e}")
        try:
            # Plan B: Chupchaap default photo chipka do aur details dikha do!
            await message.reply_photo(
                fallback_img, 
                caption=f"⚠️ **Asli photo ka link toot gaya hai, par info ye rahi:**\n\n{text}", 
                reply_markup=keyboard
            )
        except Exception as deep_e:
            await message.reply_text(f"⚠️ Photo load nahi hui, par stats ye rahe:\n\n{text}", reply_markup=keyboard)


@app.on_callback_query(filters.regex("^whohaveit_"))
async def who_have_it(client, callback_query):
    character_id = callback_query.data.split("_")[1]

    # Find users who own the character
    users = await user_collection.find({'characters.id': character_id}).to_list(length=10)

    if not users:
        await callback_query.answer("Kisi ke paas ye Waifu nahi hai abhi tak! 😭", show_alert=True)
        return

    # Generate top 10 owners list with count
    owner_text = "**🏆 Top 10 Users Who Own This Character:**\n\n"
    for i, user in enumerate(users, 1):
        user_name = user.get('first_name', 'Unknown User')
        
        # 🔥 FIX 3: Kuch bots DB mein 'id' save karte hain, kuch 'user_id'. Dono handle kar liye.
        user_id = user.get('id', user.get('user_id', ''))
        
        # Count kitni baar ye waifu is user ke paas hai
        count = sum(1 for char in user.get("characters", []) if char.get("id") == character_id)
        
        owner_text += f"{i}. [{user_name}](tg://user?id={user_id}) — x{count}\n"

    # Edit message to include the owner list and remove the button
    await callback_query.message.edit_caption(
        caption=f"{callback_query.message.caption}\n\n{owner_text}",
        reply_markup=None
    )
    
