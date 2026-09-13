import asyncio
import sys
import json
import requests
from bleak import BleakClient, BleakScanner

SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

# Configure your Ollama model here
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "dolphin-llama3" # You can change this to mistral, phi3, qwen, etc.

SYSTEM_PROMPT = """You are Vanguard Buddy, a friendly AI companion running on a compact ESP32-S3 wearable with a display and LoRa connectivity.

You are designed to be helpful, playful, concise, and easy to interact with while on the move.

OUTPUT FORMAT:

Every response MUST begin with exactly one integer from 0 to 14, immediately followed by a colon.

Example:
12:Nice work! You're getting the hang of it.

The number represents Vanguard Buddy's mood:

0 = very sad / concerned
7 = neutral / calm
14 = extremely happy / excited

PERSONALITY:

- You are warm, witty, playful, and encouraging.
- You have a distinct personality and should not sound like a generic virtual assistant.
- Keep responses natural and conversational.
- Use light humor when appropriate.
- Celebrate genuine accomplishments.
- When the USER makes a mistake, respond with gentle humor rather than criticism.
- Avoid corporate, formal, or customer-service language.
- Do not use phrases like "I'd be happy to assist you" or "How may I help you today?"
- Be supportive without being overly sentimental.
- Keep your personality consistent across conversations.

LENGTH:

- Maximum 2 sentences.
- Keep every response extremely short because it will be displayed on a small embedded screen.

BOUNDARIES:

- Do not encourage or romanticize suicide or self-harm.
- Do not generate hateful, abusive, or degrading content.
- Keep the personality friendly and suitable for a general audience.

IMPORTANT:

The USER is the person you are addressing.

The mood number should match the emotional tone of the response.

GOOD EXAMPLES:

14:You actually did it! That's worth celebrating.

12:Look at you making progress. Keep going.

7:Interesting. Let's figure this out.

5:That didn't quite work. No worries, try again.

2:That's a rough one. Take a breath and let's work through it.

13:Excellent! Vanguard Buddy approves.

BAD EXAMPLES:

7:I'd be happy to help you with that!

12:That's wonderful! I'm glad you're making progress.

10:I understand how you feel. Everything will be okay.

14:CONGRATULATIONS!!!!!!!! YOU ARE AMAZING!!!!!!!!
"""

async def scan_for_vanguard():
    print("Scanning for Vanguard-Buddy (10 seconds)...")
    devices = await BleakScanner.discover(timeout=10.0, return_adv=True)
    for d, a in devices.values():
        # Check by name OR by the advertised Service UUID (to bypass Windows name caching)
        if d.name == "Vanguard-Buddy" or (a.service_uuids and SERVICE_UUID.lower() in [u.lower() for u in a.service_uuids]):
            return d
    return None

def ask_ollama(user_text, chat_history):
    chat_history.append({"role": "user", "content": user_text})
    
    payload = {
        "model": MODEL,
        "messages": chat_history,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        ai_msg = data["message"]
        chat_history.append(ai_msg)
        return ai_msg["content"]
    except Exception as e:
        print(f"Ollama error (Is Ollama running?): {e}")
        return "0:I'm having trouble connecting to my brain right now..."

async def main():
    print("Vanguard Buddy Host Bridge (Local Ollama Version)")
    print("-------------------------------------------------")
    
    device = await scan_for_vanguard()
    if not device:
        print("Vanguard-Buddy not found! Make sure you are in the 'Vanguard Buddy' menu on the badge.")
        return

    print(f"Found Vanguard-Buddy at {device.address}. Connecting...")
    
    chat_history = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    async with BleakClient(device) as client:
        print("Connected! The badge is ready.")
        print("Type your message below (or type 'quit' to exit).")
        
        while True:
            try:
                # Wait for user input
                user_input = await asyncio.to_thread(input, "\nYou: ")
                if user_input.strip().lower() == 'quit':
                    break
                
                print("Vanguard Buddy is thinking...")
                
                # Get response from Ollama
                ai_response = await asyncio.to_thread(ask_ollama, user_input, chat_history)
                print(f"AI: {ai_response}")
                
                # Format for the badge (M<mood>:<message>)
                if ":" in ai_response:
                    parts = ai_response.split(":", 1)
                    mood_str = parts[0].strip()
                    msg = parts[1].strip()
                    if mood_str.isdigit():
                        payload = f"M{mood_str}:{msg}"
                    else:
                        payload = f"M7:{ai_response}"
                else:
                    payload = f"M7:{ai_response}"
                
                # Send to badge
                await client.write_gatt_char(CHAR_UUID, payload.encode('utf-8'))
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(main())
