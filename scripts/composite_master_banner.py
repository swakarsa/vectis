import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

def create_master_banner():
    W, H = 1920, 1080
    canvas = Image.new("RGBA", (W, H), (8, 9, 10, 255))
    
    # Fonts
    font_eyebrow = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 16)
    font_section = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 13)
    font_card_tag = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 11)
    font_card_title = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 17)
    font_card_sub = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 12)
    
    # 1. Background radial bloom
    center_x, center_y = 1350, 490
    bloom = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bloom_draw = ImageDraw.Draw(bloom)
    for r in range(550, 0, -10):
        alpha = int(28 * (1 - r / 550))
        bloom_draw.ellipse(
            [center_x - r, center_y - r, center_x + r, center_y + r],
            fill=(28, 34, 46, alpha)
        )
    bloom = bloom.filter(ImageFilter.GaussianBlur(40))
    canvas = Image.alpha_composite(canvas, bloom)
    
    # 2. Orbital rings & connecting splines
    ring_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ring_draw = ImageDraw.Draw(ring_layer)
    
    def draw_dashed_ring(cx, cy, rx, ry, num_dashes=50, dash_ratio=0.55, width=1, color=(255, 255, 255, 35)):
        step = 2 * math.pi / num_dashes
        for i in range(num_dashes):
            t_start = i * step
            t_end = t_start + step * dash_ratio
            points = []
            substeps = 8
            for s in range(substeps + 1):
                t = t_start + (t_end - t_start) * (s / substeps)
                px = cx + rx * math.cos(t)
                py = cy + ry * math.sin(t)
                points.append((px, py))
            ring_draw.line(points, fill=color, width=width)
            
    # Concentric orbital paths
    draw_dashed_ring(center_x, center_y, 520, 470, num_dashes=56, dash_ratio=0.48, width=1, color=(255, 255, 255, 32))
    draw_dashed_ring(center_x, center_y, 350, 320, num_dashes=38, dash_ratio=0.58, width=1, color=(255, 255, 255, 45))
    
    # Telemetry micro dots along orbit
    for angle in [0.25, 1.15, 2.5, 3.7, 4.6]:
        px = center_x + 520 * math.cos(angle)
        py = center_y + 470 * math.sin(angle)
        ring_draw.ellipse([px-2, py-2, px+2, py+2], fill=(255, 255, 255, 200))
        ring_draw.ellipse([px-6, py-6, px+6, py+6], fill=(255, 255, 255, 40))
        
    # Ambient cosmic dust particles
    random.seed(42)
    for _ in range(45):
        dust_x = random.randint(850, 1880)
        dust_y = random.randint(60, 1020)
        d_size = random.choice([1, 1, 2, 2, 3])
        d_alpha = random.randint(40, 140)
        ring_draw.ellipse([dust_x, dust_y, dust_x + d_size, dust_y + d_size], fill=(255, 255, 255, d_alpha))
        
    canvas = Image.alpha_composite(canvas, ring_layer)
    
    # 3. Left typography panel
    base_user_dir = "C:/Users/Hormozi/.gemini/antigravity/brain/983ab709-3483-4189-a95c-1f154bf27f3f/.user_uploaded/"
    base_frame = Image.open(base_user_dir + "media_1790416210567.png").convert("RGBA")
    
    # Crop left text region
    left_crop = base_frame.crop((0, 0, 465, base_frame.height))
    scale = H / left_crop.height
    new_w = int(left_crop.width * scale)
    left_scaled = left_crop.resize((new_w, H), Image.Resampling.LANCZOS)
    
    # Feather right edge smoothly
    feather_w = 100
    mask = Image.new("L", (new_w, H), 255)
    for x in range(new_w - feather_w, new_w):
        val = int(255 * (new_w - x) / feather_w)
        for y in range(H):
            mask.putpixel((x, y), val)
            
    canvas.paste(left_scaled, (0, 0), mask)
    
    # 3B. OVERWRITE Left Elements
    patch_draw = ImageDraw.Draw(canvas)
    
    # --- REGION 0: Eyebrow Subtitle (NO BULLET, NO EMDASH / NO LINE) ---
    # Wipe the old eyebrow area completely
    patch_draw.rectangle([80, 170, 680, 225], fill=(8, 9, 10, 255))
    
    # Pure clean letter-spaced text, no bullets, no lines
    eyebrow_text = "AUTONOMOUS RELEASE SAFETY ENGINE"
    # Spaced letters for high-end luxury look
    spaced_eyebrow = "  ".join(eyebrow_text.split()) # cleaner spacing
    patch_draw.text((95, 186), eyebrow_text, fill=(175, 182, 195, 255), font=font_eyebrow)
    
    # --- REGION 1: 3 Bottom Feature Cards (Flawless Padding & Zero Overflow) ---
    # Wipe old cards area completely
    patch_draw.rectangle([80, 660, 880, 875], fill=(8, 9, 10, 255))
    
    # Section Header
    patch_draw.text((95, 674), "TWO-TIER HYBRID ARCHITECTURE", fill=(115, 122, 136, 255), font=font_section)
    
    cards_data = [
        {
            "tag": "TIER 1 · LOCAL",
            "title": "AST Blast DAG",
            "sub": "<1.5s BFS · 0% Hallucination"
        },
        {
            "tag": "TIER 2 · BOB 2.0",
            "title": "IBM Granite 3.0",
            "sub": "FastMCP Auto-Heal Shim"
        },
        {
            "tag": "VERIFIED GATE",
            "title": "Release Passport",
            "sub": "RFC 8785 · Zero $M Outages"
        }
    ]
    
    start_x = 95
    card_w = 244
    card_h = 104
    card_gap = 16
    card_y = 712
    
    for i, c in enumerate(cards_data):
        cx = start_x + i * (card_w + card_gap)
        
        # Outer subtle card glow on hover aesthetic
        patch_draw.rounded_rectangle(
            [cx, card_y, cx + card_w, card_y + card_h],
            radius=6,
            fill=(15, 16, 19, 255),
            outline=(255, 255, 255, 24),
            width=1
        )
        
        # Top micro tag (11pt uppercase)
        patch_draw.text((cx + 18, card_y + 16), c["tag"], fill=(138, 146, 162, 255), font=font_card_tag)
        
        # Main title (17pt bold - perfect fit within 244px box)
        patch_draw.text((cx + 18, card_y + 40), c["title"], fill=(245, 247, 250, 255), font=font_card_title)
        
        # Subtitle / metric (12pt regular - generous margins)
        patch_draw.text((cx + 18, card_y + 70), c["sub"], fill=(145, 153, 168, 255), font=font_card_sub)
    
    # 4. Helper functions for 3D cards
    def load_card_with_clean_alpha(path, bg_cut=16, feather_ramp=55):
        img = Image.open(path).convert("RGBA")
        r, g, b, a = img.split()
        gray = img.convert("L")
        lut = []
        for i in range(256):
            if i <= bg_cut:
                lut.append(0)
            elif i >= feather_ramp:
                lut.append(255)
            else:
                lut.append(int(255 * (i - bg_cut) / (feather_ramp - bg_cut)))
        alpha_mask = gray.point(lut)
        img.putalpha(alpha_mask)
        return img
        
    def add_drop_shadow(target_size, blur_radius=30, opacity=200):
        sh = Image.new("RGBA", (target_size[0] + blur_radius * 4, target_size[1] + blur_radius * 4), (0, 0, 0, 0))
        sh_draw = ImageDraw.Draw(sh)
        sh_draw.rectangle([blur_radius * 2, blur_radius * 2, blur_radius * 2 + target_size[0], blur_radius * 2 + target_size[1]], fill=(0, 0, 0, opacity))
        return sh.filter(ImageFilter.GaussianBlur(blur_radius))

    # --- CARD 1: AST Contract Card (Top Left) ---
    card_ast = load_card_with_clean_alpha(base_user_dir + "media_1790416210437.png", bg_cut=16, feather_ramp=48)
    card_ast_w, card_ast_h = 430, 430
    card_ast = card_ast.resize((card_ast_w, card_ast_h), Image.Resampling.LANCZOS)
    pos_ast = (960, 110)
    
    sh_ast = add_drop_shadow((card_ast_w, card_ast_h), blur_radius=35, opacity=210)
    canvas.paste(sh_ast, (pos_ast[0] - 70, pos_ast[1] - 40), sh_ast)
    canvas.paste(card_ast, pos_ast, card_ast)
    
    # --- CARD 2: Network DAG Panel (Top Right) ---
    card_dag = load_card_with_clean_alpha(base_user_dir + "media_1790416210507.png", bg_cut=22, feather_ramp=58)
    card_dag_w, card_dag_h = 470, 470
    card_dag = card_dag.resize((card_dag_w, card_dag_h), Image.Resampling.LANCZOS)
    pos_dag = (1430, 160)
    
    sh_dag = add_drop_shadow((card_dag_w, card_dag_h), blur_radius=35, opacity=210)
    canvas.paste(sh_dag, (pos_dag[0] - 70, pos_dag[1] - 40), sh_dag)
    canvas.paste(card_dag, pos_dag, card_dag)
    
    # --- CENTRAL CORE: Titanium Folded-Ribbon V ---
    v_logo = load_card_with_clean_alpha(base_user_dir + "media_1790416210405.jpg", bg_cut=4, feather_ramp=32)
    v_size = 540
    v_logo = v_logo.resize((v_size, v_size), Image.Resampling.LANCZOS)
    pos_v = (center_x - v_size // 2 + 10, center_y - v_size // 2 - 10)
    
    # Rim-light ambient glow behind V logo
    v_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    v_glow_draw = ImageDraw.Draw(v_glow)
    v_glow_draw.ellipse([center_x - 160, center_y - 160, center_x + 160, center_y + 160], fill=(255, 255, 255, 28))
    v_glow = v_glow.filter(ImageFilter.GaussianBlur(60))
    canvas = Image.alpha_composite(canvas, v_glow)
    
    # Multi-stage drop shadow for V logo
    sh_v = add_drop_shadow((v_size, v_size), blur_radius=45, opacity=240)
    canvas.paste(sh_v, (pos_v[0] - 90, pos_v[1] - 60), sh_v)
    canvas.paste(v_logo, pos_v, v_logo)
    
    # --- CARD 3: Release Passport Card (Bottom Right) ---
    card_pass = load_card_with_clean_alpha(base_user_dir + "media_1790416210537.png", bg_cut=2, feather_ramp=24)
    card_pass_w = 480
    card_pass_h = int(card_pass_w * (card_pass.height / card_pass.width))
    card_pass = card_pass.resize((card_pass_w, card_pass_h), Image.Resampling.LANCZOS)
    pos_pass = (1300, 640)
    
    sh_pass = add_drop_shadow((card_pass_w, card_pass_h), blur_radius=40, opacity=250)
    canvas.paste(sh_pass, (pos_pass[0] - 80, pos_pass[1] - 50), sh_pass)
    canvas.paste(card_pass, pos_pass, card_pass)
    
    # 5. Vignette pass around outer edges
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vig_draw = ImageDraw.Draw(vignette)
    for i in range(120):
        alpha = int(45 * (i / 120))
        vig_draw.rectangle([i, i, W - i, H - i], outline=(8, 9, 10, alpha))
    vignette = vignette.filter(ImageFilter.GaussianBlur(25))
    canvas = Image.alpha_composite(canvas, vignette)
    
    # Save final master banner
    out_path = "d:/vectis/assets/VECTIS_OFFICIAL_16x9_HERO_BANNER.png"
    canvas.convert("RGB").save(out_path, quality=99)
    canvas.convert("RGB").save("d:/vectis/frontend/public/vectis-hero-banner-16x9.png", quality=99)
    print("SUCCESS: Master Banner updated at", out_path)

if __name__ == "__main__":
    create_master_banner()
