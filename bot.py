import os
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from pyrogram.errors import FloodWait
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

# Bot configuration
API_ID = 1234567  # Replace with your API ID
API_HASH = "your_api_hash_here"  # Replace with your API HASH
BOT_TOKEN = "your_bot_token_here"  # Replace with your bot token

# Available options
COLORS = {
    "🔴 Red": "red",
    "🔵 Blue": "blue",
    "🟢 Green": "green",
    "⚪ White": "white",
    "⚫ Black": "black",
    "🟡 Yellow": "yellow",
    "🟣 Purple": "purple"
}

POSITIONS = {
    "⬆️ Top": "top",
    "⬇️ Bottom": "bottom",
    "⬅️ Left": "left",
    "➡️ Right": "right",
    "⏺ Center": "center"
}

FONTS = {
    "🅰️ Arial": "Arial",
    "🅱️ Bahnschrift": "Bahnschrift",
    "🅲️ Calibri": "Calibri",
    "🅳️ David": "David",
    "🅴️ Ebrima": "Ebrima"
}

# Initialize the Pyrofork client
app = Client(
    "video_watermark_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

class Progress:
    def __init__(self, message, start_time, operation):
        self.message = message
        self.start_time = start_time
        self.operation = operation
    
    async def __call__(self, current, total):
        try:
            percent = current * 100 / total
            elapsed_time = time.time() - self.start_time
            speed = current / elapsed_time if elapsed_time > 0 else 0
            
            progress_bar = "[" + "■" * int(percent / 5) + " " * (20 - int(percent / 5)) + "]"
            
            speed_text = ""
            if speed > 1024 * 1024:
                speed_text = f"{speed / (1024 * 1024):.2f} MB/s"
            elif speed > 1024:
                speed_text = f"{speed / 1024:.2f} KB/s"
            else:
                speed_text = f"{speed:.2f} B/s"
            
            text = (
                f"**{self.operation}...**\n"
                f"{progress_bar} {percent:.2f}%\n"
                f"**Speed:** {speed_text}\n"
                f"**Processed:** {human_readable_size(current)} / {human_readable_size(total)}"
            )
            
            await self.message.edit_text(text)
        except FloodWait as e:
            time.sleep(e.value)
        except Exception:
            pass

def human_readable_size(size):
    units = ["B", "KB", "MB", "GB"]
    unit_index = 0
    while size >= 1024 and unit_index < len(units)-1:
        size /= 1024
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"

def add_watermark(video_path, output_path, watermark_text, color, position, font):
    try:
        video = VideoFileClip(video_path)
        
        # Position mapping
        pos_mapping = {
            "top": ("center", "top"),
            "bottom": ("center", "bottom"),
            "left": ("left", "center"),
            "right": ("right", "center"),
            "center": ("center", "center")
        }
        
        txt_clip = TextClip(
            watermark_text,
            fontsize=50,
            color=color,
            font=font,
            stroke_color='black',
            stroke_width=1
        )
        txt_clip = txt_clip.set_position(pos_mapping[position])
        txt_clip = txt_clip.set_duration(video.duration)
        txt_clip = txt_clip.set_opacity(0.7)
        
        final_clip = CompositeVideoClip([video, txt_clip])
        
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='ultrafast',
            logger=None
        )
        
        return True
    except Exception as e:
        print(f"Error in watermarking: {e}")
        return False
    finally:
        if 'video' in locals():
            video.close()
        if 'final_clip' in locals():
            final_clip.close()
        if 'txt_clip' in locals():
            txt_clip.close()

user_states = {}

@app.on_message(filters.command(["start", "help"]))
async def welcome(client: Client, message: Message):
    welcome_text = """
    🎥 **Advanced Video Watermark Bot** 🎥

    Send me a video and I'll add a customized text watermark!

    **Features:**
    - Multiple text colors
    - Different positions (top, bottom, left, right, center)
    - Various font styles
    - Fast processing

    Just send me a video to get started!
    """
    await message.reply_text(welcome_text)

@app.on_message(filters.video | filters.document)
async def handle_video(client: Client, message: Message):
    if message.document and not message.document.mime_type.startswith("video/"):
        return
    
    user_states[message.from_user.id] = {
        "video_message": message,
        "step": "waiting_for_text"
    }
    
    await message.reply_text("Please send the text you want to use as watermark:")

@app.on_message(filters.text & filters.private)
async def handle_text(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return
    
    if user_states[user_id]["step"] == "waiting_for_text":
        user_states[user_id]["watermark_text"] = message.text
        user_states[user_id]["step"] = "waiting_for_color"
        
        # Create color selection keyboard
        color_buttons = [InlineKeyboardButton(text, callback_data=data) for text, data in COLORS.items()]
        keyboard = [color_buttons[i:i + 2] for i in range(0, len(color_buttons), 2)]
        
        await message.reply_text(
            "Please choose a text color:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif user_states[user_id]["step"] == "waiting_for_font":
        # This handles font selection if we had a text input for fonts
        pass

@app.on_callback_query()
async def handle_callback(client: Client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in user_states:
        return
    
    data = callback_query.data
    
    if user_states[user_id]["step"] == "waiting_for_color":
        if data in COLORS.values():
            user_states[user_id]["color"] = data
            user_states[user_id]["step"] = "waiting_for_position"
            
            # Create position selection keyboard
            position_buttons = [InlineKeyboardButton(text, callback_data=data) for text, data in POSITIONS.items()]
            keyboard = [position_buttons[i:i + 3] for i in range(0, len(position_buttons), 3)]
            
            await callback_query.message.edit_text(
                "Please choose watermark position:",
                reply_markup=InlineKeyboardMarkup(keyboard)
    
    elif user_states[user_id]["step"] == "waiting_for_position":
        if data in POSITIONS.values():
            user_states[user_id]["position"] = data
            user_states[user_id]["step"] = "waiting_for_font"
            
            # Create font selection keyboard
            font_buttons = [InlineKeyboardButton(text, callback_data=data) for text, data in FONTS.items()]
            keyboard = [font_buttons[i:i + 3] for i in range(0, len(font_buttons), 3)]
            
            await callback_query.message.edit_text(
                "Please choose a font style:",
                reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif user_states[user_id]["step"] == "waiting_for_font":
        if data in FONTS.values():
            user_states[user_id]["font"] = data
            
            # All options selected, start processing
            video_message = user_states[user_id]["video_message"]
            watermark_text = user_states[user_id]["watermark_text"]
            color = user_states[user_id]["color"]
            position = user_states[user_id]["position"]
            font = user_states[user_id]["font"]
            
            processing_msg = await callback_query.message.reply_text("📥 Downloading video...")
            start_time = time.time()
            
            video_path = f"downloads/{user_id}_{video_message.id}.mp4"
            os.makedirs("downloads", exist_ok=True)
            
            await video_message.download(
                file_name=video_path,
                progress=Progress(processing_msg, start_time, "Downloading")
            )
            
            await processing_msg.edit_text("🔄 Adding watermark...")
            output_path = f"downloads/{user_id}_{video_message.id}_watermarked.mp4"
            
            if not add_watermark(video_path, output_path, watermark_text, color, position, font):
                await processing_msg.edit_text("❌ Failed to add watermark. Please try again.")
                try:
                    os.remove(video_path)
                    os.remove(output_path)
                except:
                    pass
                return
            
            await processing_msg.edit_text("📤 Uploading watermarked video...")
            upload_start_time = time.time()
            
            await callback_query.message.reply_video(
                video=output_path,
                caption=f"Watermarked with: {watermark_text}\nColor: {color}\nPosition: {position}\nFont: {font}",
                progress=Progress(processing_msg, upload_start_time, "Uploading")
            )
            
            await processing_msg.delete()
            
            try:
                os.remove(video_path)
                os.remove(output_path)
            except:
                pass
            
            del user_states[user_id]

if __name__ == "__main__":
    print("Bot is running...")
    app.run()
