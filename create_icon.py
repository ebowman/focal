#!/usr/bin/env python3
"""Create a professional icon for the Fantastical AI Calendar workflow."""

from PIL import Image, ImageDraw, ImageFont
import math

def create_icon():
    """Create a calendar icon with AI badge."""
    
    # Create a 512x512 image (will be resized as needed)
    size = 512
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    bg_gradient_start = '#4A90E2'  # Blue
    bg_gradient_end = '#357ABD'    # Darker blue
    white = '#FFFFFF'
    red = '#FF4444'
    ai_gold = '#FFD700'
    shadow = (0, 0, 0, 30)
    
    # Create rounded rectangle background
    corner_radius = 80
    # Draw main background
    draw.rounded_rectangle(
        [(40, 40), (size-40, size-40)],
        radius=corner_radius,
        fill=bg_gradient_start
    )
    
    # Calendar header (red bar at top)
    draw.rounded_rectangle(
        [(40, 40), (size-40, 140)],
        radius=corner_radius,
        fill=red
    )
    # Square off the bottom of header
    draw.rectangle(
        [(40, 100), (size-40, 140)],
        fill=red
    )
    
    # Calendar grid
    grid_start_y = 180
    grid_start_x = 80
    grid_end_x = size - 80
    grid_end_y = size - 80
    cell_width = (grid_end_x - grid_start_x) / 7
    cell_height = (grid_end_y - grid_start_y) / 5
    
    # Draw day labels (S M T W T F S)
    days = ['S', 'M', 'T', 'W', 'T', 'F', 'S']
    try:
        font_day = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
    except:
        font_day = ImageFont.load_default()
    
    for i, day in enumerate(days):
        x = grid_start_x + i * cell_width + cell_width/2
        y = 150
        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), day, font=font_day)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text((x - text_width/2, y), day, fill=white, font=font_day)
    
    # Draw grid lines
    line_width = 3
    
    # Horizontal lines
    for i in range(6):
        y = grid_start_y + i * cell_height
        draw.line([(grid_start_x, y), (grid_end_x, y)], fill=white, width=line_width)
    
    # Vertical lines
    for i in range(8):
        x = grid_start_x + i * cell_width
        draw.line([(x, grid_start_y), (x, grid_end_y)], fill=white, width=line_width)
    
    # Add some date numbers
    try:
        font_date = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    except:
        font_date = ImageFont.load_default()
    
    # Sample dates
    date = 1
    for row in range(5):
        for col in range(7):
            if date <= 31:
                x = grid_start_x + col * cell_width + 10
                y = grid_start_y + row * cell_height + 10
                # Highlight today (15th)
                if date == 15:
                    # Draw highlight circle
                    cx = grid_start_x + col * cell_width + cell_width/2
                    cy = grid_start_y + row * cell_height + cell_height/2
                    draw.ellipse(
                        [(cx-25, cy-25), (cx+25, cy+25)],
                        fill=ai_gold
                    )
                    draw.text((x+5, y), str(date), fill='#333333', font=font_date)
                else:
                    draw.text((x, y), str(date), fill=white, font=font_date)
                date += 1
    
    # Add "AI" badge in corner
    badge_size = 120
    badge_x = size - badge_size - 30
    badge_y = size - badge_size - 30
    
    # Badge background circle with glow
    for i in range(3, 0, -1):
        glow_size = badge_size + i * 10
        glow_x = badge_x - i * 5
        glow_y = badge_y - i * 5
        alpha = 40 - i * 10
        draw.ellipse(
            [(glow_x, glow_y), (glow_x + glow_size, glow_y + glow_size)],
            fill=(255, 215, 0, alpha)
        )
    
    draw.ellipse(
        [(badge_x, badge_y), (badge_x + badge_size, badge_y + badge_size)],
        fill=ai_gold
    )
    
    # AI text
    try:
        font_ai = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48, encoding="unic")
    except:
        font_ai = ImageFont.load_default()
    
    ai_text = "AI"
    bbox = draw.textbbox((0, 0), ai_text, font=font_ai)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = badge_x + badge_size/2 - text_width/2
    text_y = badge_y + badge_size/2 - text_height/2 - 5
    draw.text((text_x, text_y), ai_text, fill='#333333', font=font_ai)
    
    # Save multiple sizes
    # Alfred uses 256x256 for display
    img_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
    img_256.save('workflow/icon.png')
    
    # Also save original for documentation
    img.save('icon.png')
    
    print("✅ Created professional calendar + AI icon")
    print("  • workflow/icon.png (256x256) - for Alfred")
    print("  • icon.png (512x512) - for documentation")

if __name__ == "__main__":
    create_icon()