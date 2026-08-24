from PIL import Image
import sys
import os

def convert(filename, out_filename):
    img = Image.open(filename).convert("RGB")
    
    # Scale down the image so it fits nicely on a 320x240 screen (max 100x100 bounding box)
    # Using NEAREST to preserve crisp pixel-art edges
    img.thumbnail((100, 100), Image.Resampling.NEAREST)
    
    width, height = img.size
    
    with open(out_filename, "w") as f:
        f.write("#pragma once\n")
        f.write("#include <cstdint>\n")
        f.write("#include <pgmspace.h>\n\n")
        f.write(f"constexpr int MIKU_WIDTH = {width};\n")
        f.write(f"constexpr int MIKU_HEIGHT = {height};\n\n")
        f.write(f"constexpr uint16_t MIKU_BITMAP[{width * height}] PROGMEM = {{\n  ")
        
        count = 0
        for y in range(height):
            for x in range(width):
                r, g, b = img.getpixel((x, y))
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                
                f.write(f"0x{rgb565:04X}, ")
                count += 1
                if count % 16 == 0:
                    f.write("\n  ")
        f.write("\n};\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_image.py <image.png>")
        sys.exit(1)
        
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_path = os.path.join(project_root, "firmware", "main", "girlfriend", "miku_data.h")
    convert(sys.argv[1], out_path)
    print(f"Generated {out_path}!")
