import asyncio
import sys
from bleak import BleakClient, BleakScanner

SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

async def scan_for_vanguard():
    print("Scanning for Vanguard-GF...")
    devices = await BleakScanner.discover()
    for d in devices:
        if d.name == "Vanguard-GF":
            return d
    return None

async def main():
    print("AI Girlfriend Host Bridge")
    print("-------------------------")
    
    device = await scan_for_vanguard()
    if not device:
        print("Vanguard-GF not found! Make sure you are in the 'AI Girlfriend' menu on the badge.")
        return

    print(f"Found Vanguard-GF at {device.address}. Connecting...")
    
    async with BleakClient(device) as client:
        print("Connected!")
        print("Enter message to send, or 'quit' to exit.")
        print("Format: <mood_0_14>:<message>")
        print("Example: 7:Hello Vanguard!")
        
        while True:
            try:
                # Need to use an async input or thread, but for hackathon a simple blocking input in loop is fine
                # as long as connection doesn't drop. For a real app, use aioconsole or threads.
                user_input = await asyncio.to_thread(input, ">>> ")
                if user_input.strip().lower() == 'quit':
                    break
                
                # Format to M<mood>:<message> if the user just typed "7:Hello"
                # We'll prepend 'M' to match what Vanguard expects.
                if ":" in user_input:
                    parts = user_input.split(":", 1)
                    if parts[0].isdigit():
                        payload = f"M{user_input}"
                    else:
                        payload = f"M0:{user_input}"
                else:
                    payload = f"M0:{user_input}"
                
                await client.write_gatt_char(CHAR_UUID, payload.encode('utf-8'))
                print(f"Sent: {payload}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(main())
