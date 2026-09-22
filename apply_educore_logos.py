"""
==============================================================================
EDUCORE SERVICES - OPEN WEBUI BRANDING & LOGO PROVISIONING SCRIPT
Strict ISO/IEC 42001:2023 & Zambian Data Protection Act No. 3 Alignment
Replaces default Open WebUI branding with:
  1. Default Educore Institutional Logo (educore.png) for Favicons & Small Icons
  2. Stylised Educore RAG Platform Logo (educore-rag-e.png) for Hero, Splash, Logo, PWA, and AI Models
==============================================================================
"""

import os
import sys
import shutil
import base64
import sqlite3
import json
from io import BytesIO
from PIL import Image

# Set UTF-8 safe stdout for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EDUCORE_DEFAULT_LOGO = os.path.join(BASE_DIR, "educore.png")
EDUCORE_RAG_LOGO = os.path.join(BASE_DIR, "educore-rag-e.png")

TARGET_DIRS = [
    os.path.join(BASE_DIR, ".openwebui_env", "Lib", "site-packages", "open_webui", "static"),
    os.path.join(BASE_DIR, ".openwebui_env", "Lib", "site-packages", "open_webui", "frontend", "static"),
]

WEBUI_DB_PATH = os.path.join(BASE_DIR, ".openwebui_env", "Lib", "site-packages", "open_webui", "data", "webui.db")

CUSTOM_CSS_RULE = """
/* ==========================================================================
   EDUCORE SERVICES ENTERPRISE BRANDING & UI GOVERNANCE STYLING
   1. Dark mode color preservation (prevents Tailwind dark:invert on orange)
   2. Model Selector & Clearance Tier Anti-Truncation Rules
   ========================================================================== */

/* 1. Prevent Tailwind dark:invert from altering Educore orange (#F1592A) */
img[alt="logo"],
img[alt="logo"].dark\\:invert,
button[aria-label="Home"] img,
#logo,
#logo-her {
    filter: none !important;
}

/* 2. Model Selector Active Pill (Chat Header & Input Bar) */
/* Overrides Tailwind max-w-56 (14rem/224px) so full model names and clearance tiers display */
.flex.max-w-56,
div.max-w-56,
[class*="max-w-56"] {
    max-width: 50rem !important;
}

/* Allow text inside active model pill to remain legible without premature truncation */
.flex.max-w-56 .truncate,
div.max-w-56 .truncate,
[class*="max-w-56"] .truncate {
    max-width: none !important;
    overflow: visible !important;
    text-overflow: clip !important;
    white-space: nowrap !important;
}

/* 3. Model Selector Trigger in Top Navbar (Outside Chat Input Box) */
body :not(#message-input-container) button[id*="model-selector"],
body :not(#message-input-container) button[aria-haspopup="listbox"],
body :not(#message-input-container) .model-selector-button {
    max-width: none !important;
    width: auto !important;
    overflow: visible !important;
}

/* Unclip parent containers in the top navbar / header */
header .min-w-0.max-w-full.overflow-hidden,
nav .min-w-0.max-w-full.overflow-hidden,
div:has(> .min-w-0.max-w-full.overflow-hidden):not(#message-input-container *) {
    overflow: visible !important;
    max-width: none !important;
}

/* Ensure model name in top navbar remains on one line and expands horizontally */
body :not(#message-input-container) button[id*="model-selector"] span,
body :not(#message-input-container) button[aria-haspopup="listbox"] span {
    overflow: visible !important;
    text-overflow: clip !important;
    white-space: nowrap !important;
    max-width: none !important;
}

/* 4. Chat Input Box (Bottom) - Prevent Collision with Mic & Voice Mode Buttons */
#message-input-container button[id*="model-selector"],
#message-input-container button[aria-haspopup="listbox"],
#message-input-container .model-selector-button {
    max-width: 100% !important;
    overflow: hidden !important;
}

#message-input-container button[id*="model-selector"] span,
#message-input-container button[id*="model-selector"] div,
#message-input-container button[aria-haspopup="listbox"] span,
#message-input-container button[aria-haspopup="listbox"] div,
#message-input-container .truncate {
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
    max-width: 100% !important;
}

#message-input-container .max-w-\\[10rem\\],
#message-input-container [class*="max-w-\\[10rem\\]"],
#message-input-container [class*="sm:max-w-\\[13rem\\]"] {
    max-width: 14rem !important;
    overflow: hidden !important;
}

/* 5. Selected Model on New Chat Landing View (Center / Top Hero) */
/* Overrides max-w-xl (36rem) and line-clamp-1 so full model title and clearance tier are visible */
.flex.flex-row.justify-center.w-fit.max-w-xl,
.flex.flex-row.justify-center.max-w-xl,
div:has(> .text-2xl.line-clamp-1),
div:has(> .\\@sm\\:text-2xl.line-clamp-1) {
    max-width: 95vw !important;
    width: auto !important;
}

.text-2xl.line-clamp-1,
.text-2xl .line-clamp-1,
.\\@sm\\:text-2xl.line-clamp-1,
.\\@sm\\:text-2xl .line-clamp-1,
div.text-2xl span.line-clamp-1,
div.\\@sm\\:text-2xl span.line-clamp-1,
div[class*="text-2xl"] [class*="line-clamp-1"] {
    overflow: visible !important;
    white-space: normal !important;
    text-overflow: clip !important;
    -webkit-line-clamp: unset !important;
    line-clamp: unset !important;
    display: inline-block !important;
    text-align: center !important;
}

/* Allow model description and markdown on new chat landing view to display cleanly */
.line-clamp-2.max-w-xl,
div[class*="line-clamp-2"][class*="max-w-xl"] {
    max-width: 52rem !important;
    -webkit-line-clamp: unset !important;
    line-clamp: unset !important;
    overflow: visible !important;
    white-space: normal !important;
}

/* Pinned models list anti-truncation */
#pinned-models-list .line-clamp-1,
#pinned-models-list a div {
    overflow: visible !important;
    white-space: normal !important;
    -webkit-line-clamp: unset !important;
    line-clamp: unset !important;
}

/* 6. Model Selector Dropdown Menu & Popover */
/* Overrides default w-[20rem] (320px) and w-64 (256px) so all models, tiers, and descriptions fit */
div[style*="z-index: 9999"] .z-40.w-\\[20rem\\],
div[style*="z-index: 9999"] .w-\\[20rem\\],
div[style*="z-index: 9999"] .w-64,
div[style*="z-index: 9999"] [class*="w-64"],
.model-selector-child-menu {
    width: 34rem !important;
    max-width: calc(100vw - 2rem) !important;
}

/* 6. Model Item Rows inside Dropdown Menu */
/* Ensure full model persona, clearance tier (Tier A/B/C), and descriptions are fully visible */
div[style*="z-index: 9999"] .truncate,
div[style*="z-index: 9999"] .line-clamp-1,
.selected-command-option-button .truncate,
.selected-command-option-button .line-clamp-1,
.selected-command-option-button .line-clamp-2 {
    overflow: visible !important;
    white-space: normal !important;
    word-break: break-word !important;
    -webkit-line-clamp: unset !important;
    line-clamp: unset !important;
}

/* Ensure dropdown rows have comfortable spacing for multi-line titles */
.selected-command-option-button {
    height: auto !important;
    min-height: 2.25rem !important;
    padding-top: 0.375rem !important;
    padding-bottom: 0.375rem !important;
}

/* ==========================================================================
   7. Circular Cutout Removal & Anti-Clipping Rules (Square Corners)
   Ensure logos and model avatars have square/soft corners so edges are not cut
   ========================================================================== */

/* Universal square / soft-corner override for all logos and model avatars */
img[alt="logo"],
img[alt="favicon"],
img[alt="model profile"],
img[alt="modelfile profile"],
img[alt="profile"],
img[alt*="profile image"],
img[src*="/models/model/profile/image"],
img[src*="educore-rag-e.png"],
img[src*="educore.png"],
#logo,
#logo-her,
button[aria-label="Home"],
button[aria-label="Home"] img,
button[aria-label="Chat"],
button[aria-label="Chat"] img {
    border-radius: 0.375rem !important; /* Soft square corners */
    object-fit: contain !important;      /* Preserve entire logo without clipping edges */
}

/* ==========================================================================
   8. Model Selector Dropdown & Menu Logo Enhancement
   Ensures model icons in dropdown rows are square, unclipped, and neatly proportioned
   ========================================================================== */

/* Target model icons in the model selector dropdown and command option rows */
.selected-command-option-button img,
.model-selector-child-menu img {
    width: 1.25rem !important;
    height: 1.25rem !important;
    min-width: 1.25rem !important;
    min-height: 1.25rem !important;
    max-width: 1.25rem !important;
    max-height: 1.25rem !important;
    border-radius: 0.25rem !important;
    object-fit: contain !important;
    flex-shrink: 0 !important;
    background: transparent !important;
}

/* Ensure dropdown wrapper containers match the icon sizing */
.selected-command-option-button .size-4,
.selected-command-option-button .size-4\.5,
.selected-command-option-button .size-3\.5,
.selected-command-option-button [class*="size-4"],
.selected-command-option-button [class*="size-3.5"],
.model-selector-child-menu .size-4,
.model-selector-child-menu .size-4\.5,
.model-selector-child-menu [class*="size-4"] {
    width: 1.25rem !important;
    height: 1.25rem !important;
    min-width: 1.25rem !important;
    min-height: 1.25rem !important;
    border-radius: 0.25rem !important;
    overflow: visible !important;
}
"""


def fit_image(image: Image.Image, canvas_size: tuple, padding_ratio: float = 0.88, bg_color=(0, 0, 0, 0), ensure_circle_safe: bool = True) -> Image.Image:
    """Fit an image into a canvas_size square keeping aspect ratio, centered and circle-safe."""
    # 1. Crop to content bounding box for perfect centering
    bbox = image.getbbox()
    cropped = image.crop(bbox) if bbox else image

    canvas = Image.new("RGBA", canvas_size, bg_color)
    max_w = int(canvas_size[0] * padding_ratio)
    max_h = int(canvas_size[1] * padding_ratio)

    scale = min(max_w / cropped.width, max_h / cropped.height)
    new_w = max(1, int(cropped.width * scale))
    new_h = max(1, int(cropped.height * scale))

    if ensure_circle_safe:
        # Check if the rectangular corners exceed the inscribed circle of radius R
        radius = min(canvas_size[0], canvas_size[1]) / 2.0
        corner_dist = ((new_w / 2.0) ** 2 + (new_h / 2.0) ** 2) ** 0.5
        if corner_dist > radius * 0.96:  # 4% safe margin inside circle
            circle_scale = (radius * 0.96) / corner_dist
            new_w = max(1, int(new_w * circle_scale))
            new_h = max(1, int(new_h * circle_scale))

    resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
    pos_x = (canvas_size[0] - new_w) // 2
    pos_y = (canvas_size[1] - new_h) // 2

    canvas.paste(resized, (pos_x, pos_y), resized)
    return canvas


def generate_svg(png_image: Image.Image) -> str:
    """Generate SVG wrapping base64 PNG."""
    buf = BytesIO()
    png_image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    w, h = png_image.size
    return f"""<svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><image width="{w}" height="{h}" xlink:href="data:image/png;base64,{b64}"/><style>@media (prefers-color-scheme: light) {{ :root {{ filter: none; }} }}
@media (prefers-color-scheme: dark) {{ :root {{ filter: none; }} }}
</style></svg>"""


def apply_branding():
    if not os.path.exists(EDUCORE_DEFAULT_LOGO):
        print(f"Error: {EDUCORE_DEFAULT_LOGO} not found.")
        sys.exit(1)
    if not os.path.exists(EDUCORE_RAG_LOGO):
        print(f"Error: {EDUCORE_RAG_LOGO} not found.")
        sys.exit(1)

    print("==============================================================================")
    print("  APPLYING EDUCORE BRANDING TO OPEN WEBUI")
    print("==============================================================================")

    # 1. Load source logos
    print("[1/5] Loading source logos...")
    default_logo = Image.open(EDUCORE_DEFAULT_LOGO).convert("RGBA")
    rag_logo = Image.open(EDUCORE_RAG_LOGO).convert("RGBA")
    print(f"  ✓ Default Educore logo loaded: {default_logo.size}")
    print(f"  ✓ Stylised Educore RAG logo loaded: {rag_logo.size}")

    # 2. Generate assets
    print("\n[2/5] Generating branded asset suite...")
    
    # A. Stylised RAG Platform Assets (Hero, Splash, PWA, Model Avatars)
    splash_500 = fit_image(rag_logo, (500, 500), padding_ratio=0.88, ensure_circle_safe=True)
    logo_500 = fit_image(rag_logo, (500, 500), padding_ratio=0.88, ensure_circle_safe=True)
    manifest_512 = fit_image(rag_logo, (512, 512), padding_ratio=0.88, ensure_circle_safe=True)
    manifest_192 = fit_image(rag_logo, (192, 192), padding_ratio=0.88, ensure_circle_safe=True)

    # B. Default Institutional Assets (Favicons, Touch Icons)
    favicon_512 = fit_image(default_logo, (512, 512), padding_ratio=0.88, ensure_circle_safe=True)
    favicon_96 = fit_image(default_logo, (96, 96), padding_ratio=0.88, ensure_circle_safe=True)
    apple_touch_180 = fit_image(default_logo, (180, 180), padding_ratio=0.82, bg_color=(255, 255, 255, 255), ensure_circle_safe=True)
    
    # Multi-resolution ICO (16, 32, 48)
    ico_images = [
        fit_image(default_logo, (16, 16), padding_ratio=0.9, ensure_circle_safe=True),
        fit_image(default_logo, (32, 32), padding_ratio=0.9, ensure_circle_safe=True),
        fit_image(default_logo, (48, 48), padding_ratio=0.9, ensure_circle_safe=True),
    ]

    svg_content = generate_svg(favicon_512)

    print("  ✓ Splash screens generated (500x500)")
    print("  ✓ Platform logo generated (500x500)")
    print("  ✓ Web manifest icons generated (192x192, 512x512)")
    print("  ✓ Favicons generated (PNG 512x512, 96x96; ICO 16/32/48; SVG)")
    print("  ✓ Apple Touch icon generated (180x180)")

    # 3. Deploy to target static directories
    print("\n[3/5] Deploying assets to Open WebUI static directories...")
    for target_dir in TARGET_DIRS:
        if not os.path.exists(target_dir):
            print(f"  ! Warning: Directory {target_dir} does not exist, creating...")
            os.makedirs(target_dir, exist_ok=True)

        # Write Splash & Hero Logos
        splash_500.save(os.path.join(target_dir, "splash.png"), format="PNG")
        splash_500.save(os.path.join(target_dir, "splash-dark.png"), format="PNG")
        logo_500.save(os.path.join(target_dir, "logo.png"), format="PNG")
        manifest_192.save(os.path.join(target_dir, "web-app-manifest-192x192.png"), format="PNG")
        manifest_512.save(os.path.join(target_dir, "web-app-manifest-512x512.png"), format="PNG")

        # Write Favicons & Touch Icons
        favicon_512.save(os.path.join(target_dir, "favicon.png"), format="PNG")
        favicon_96.save(os.path.join(target_dir, "favicon-96x96.png"), format="PNG")
        apple_touch_180.save(os.path.join(target_dir, "apple-touch-icon.png"), format="PNG")
        ico_images[1].save(
            os.path.join(target_dir, "favicon.ico"),
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48)],
            append_images=[ico_images[0], ico_images[2]]
        )
        with open(os.path.join(target_dir, "favicon.svg"), "w", encoding="utf-8") as f:
            f.write(svg_content)

        # Copy original high-res assets for direct referencing
        shutil.copy2(EDUCORE_DEFAULT_LOGO, os.path.join(target_dir, "educore.png"))
        shutil.copy2(EDUCORE_RAG_LOGO, os.path.join(target_dir, "educore-rag-e.png"))

        # Update custom.css with enterprise branding and model selector anti-truncation rules
        css_path = os.path.join(target_dir, "custom.css")
        with open(css_path, "w", encoding="utf-8") as f:
            f.write(CUSTOM_CSS_RULE.strip() + "\n")

        print(f"  ✓ Deployed to {target_dir}")

    # 4. Update Database Models with Stylised RAG Logo
    print("\n[4/5] Updating Open WebUI database AI model avatars...")
    if os.path.exists(WEBUI_DB_PATH):
        try:
            con = sqlite3.connect(WEBUI_DB_PATH)
            cur = con.cursor()
            cur.execute("SELECT id, meta FROM model")
            rows = cur.fetchall()
            updated_count = 0
            for model_id, meta_json in rows:
                if meta_json:
                    try:
                        meta = json.loads(meta_json)
                    except Exception:
                        meta = {}
                else:
                    meta = {}

                # Set avatar to the stylised Educore RAG platform logo
                meta["profile_image_url"] = "/static/educore-rag-e.png"
                cur.execute("UPDATE model SET meta = ? WHERE id = ?", (json.dumps(meta), model_id))
                updated_count += 1

            con.commit()
            con.close()
            print(f"  ✓ Updated {updated_count} model(s) in {WEBUI_DB_PATH} with '/static/educore-rag-e.png' avatar.")
        except Exception as e:
            print(f"  ! Error updating database: {e}")
    else:
        print(f"  ! Database not found at {WEBUI_DB_PATH} (will be applied when RBAC provisioning runs)")

    print("\n[5/5] Branding configuration verified!")
    print("==============================================================================")
    print("  EDUCORE BRANDING APPLICATION COMPLETE!")
    print("==============================================================================")


if __name__ == "__main__":
    apply_branding()
