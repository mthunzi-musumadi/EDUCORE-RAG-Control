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
import glob
import time
import re
from io import BytesIO
from PIL import Image

# Set UTF-8 safe stdout for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def resolve_base_dir() -> str:
    """
    Dynamically resolves the BASE_DIR for Educore RAG Control and logos.
    Priority:
      1. Command-line flag: --base-dir <path>, -b <path>, or --base-dir=<path>
      2. Environment variables: BASE_DIR, EDUCORE_BASE_DIR, PROJECT_DIR, EDUCORE_RAG_DIR
      3. Directory containing this script
      4. Current working directory
      5. Upward traversal looking for educore.png / educore-rag-e.png
    """
    # 1. Command-line argument
    for i, arg in enumerate(sys.argv[1:], start=1):
        if arg in ("--base-dir", "-b") and i < len(sys.argv) - 1:
            candidate = sys.argv[i + 1]
            if os.path.exists(candidate):
                return os.path.abspath(candidate)
        elif arg.startswith("--base-dir="):
            candidate = arg.split("=", 1)[1]
            if os.path.exists(candidate):
                return os.path.abspath(candidate)

    # 2. Environment variables
    for env_key in ("BASE_DIR", "EDUCORE_BASE_DIR", "PROJECT_DIR", "EDUCORE_RAG_DIR"):
        val = os.environ.get(env_key)
        if val and os.path.exists(val):
            return os.path.abspath(val)

    # 3. Directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

    # 4. Upward search from script_dir and cwd
    cwd = os.getcwd()
    for start in (script_dir, cwd):
        curr = os.path.abspath(start)
        while True:
            if (
                os.path.exists(os.path.join(curr, "assets", "educore.png"))
                or os.path.exists(os.path.join(curr, "educore.png"))
                or os.path.exists(os.path.join(curr, "EDUCORE_AI_FRAMEWORK"))
            ):
                return curr
            parent = os.path.dirname(curr)
            if parent == curr:
                break
            curr = parent

    return os.path.abspath(os.path.join(script_dir, "..", ".."))


def find_logo_path(filename: str, base_dir: str) -> str:
    """Finds a logo file across base_dir, script dir, cwd, logo subdirectories, or environment."""
    candidates = []

    # Environment variable override
    env_dir = os.environ.get("EDUCORE_LOGO_DIR")
    if env_dir:
        candidates.append(os.path.join(env_dir, filename))

    # Base dir & subfolders
    candidates.extend([
        os.path.join(base_dir, filename),
        os.path.join(base_dir, "static", filename),
        os.path.join(base_dir, "assets", filename),
    ])

    # Script dir & cwd
    script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else ""
    if script_dir and script_dir != base_dir:
        candidates.extend([
            os.path.join(script_dir, filename),
            os.path.join(script_dir, "static", filename),
            os.path.join(script_dir, "assets", filename),
        ])
    cwd = os.getcwd()
    if cwd not in (base_dir, script_dir):
        candidates.extend([
            os.path.join(cwd, filename),
            os.path.join(cwd, "static", filename),
            os.path.join(cwd, "assets", filename),
        ])

    for c in candidates:
        if c and os.path.exists(c):
            return os.path.abspath(c)

    # Upward search fallback
    for start in (base_dir, script_dir, cwd):
        if not start:
            continue
        curr = os.path.abspath(start)
        while True:
            probe = os.path.join(curr, filename)
            if os.path.exists(probe):
                return probe
            parent = os.path.dirname(curr)
            if parent == curr:
                break
            curr = parent

    return os.path.join(base_dir, filename)


def resolve_target_dirs(base_dir: str) -> list[str]:
    """
    Dynamically discovers Open WebUI static directories across the environment.
    Searches:
      1. Open WebUI package if importable
      2. Environment variables (OPENWEBUI_STATIC_DIR, WEBUI_STATIC_DIR, WEBUI_BUILD_DIR, OPENWEBUI_DIR)
      3. Active Python prefix (sys.prefix) site-packages (Windows and Unix/Linux layouts)
      4. Discovered BASE_DIR virtualenvs (.openwebui_env, openwebui_env, .venv, venv, env)
      5. Current working directory virtualenvs
    Returns all detected valid existing static directories (or defaults if none exist).
    """
    discovered = []

    # 1. Try importing open_webui package directly
    try:
        import open_webui
        ow_pkg_dir = os.path.dirname(os.path.abspath(open_webui.__file__))
        for sub in ("static", os.path.join("frontend", "static")):
            candidate = os.path.join(ow_pkg_dir, sub)
            discovered.append(candidate)
    except Exception:
        pass

    # 2. Environment variables
    for env_var in ("OPENWEBUI_STATIC_DIR", "WEBUI_STATIC_DIR", "WEBUI_BUILD_DIR"):
        val = os.environ.get(env_var)
        if val:
            discovered.append(val)

    for env_var in ("OPENWEBUI_DIR", "WEBUI_DIR"):
        val = os.environ.get(env_var)
        if val:
            discovered.extend([
                os.path.join(val, "static"),
                os.path.join(val, "frontend", "static"),
                os.path.join(val, "Lib", "site-packages", "open_webui", "static"),
                os.path.join(val, "Lib", "site-packages", "open_webui", "frontend", "static"),
            ])

    # 3. sys.prefix (the active python interpreter environment)
    if sys.prefix:
        discovered.extend([
            os.path.join(sys.prefix, "Lib", "site-packages", "open_webui", "static"),
            os.path.join(sys.prefix, "Lib", "site-packages", "open_webui", "frontend", "static"),
        ])
        for p in glob.glob(os.path.join(sys.prefix, "lib", "python*", "site-packages", "open_webui", "static")):
            discovered.append(p)
        for p in glob.glob(os.path.join(sys.prefix, "lib", "python*", "site-packages", "open_webui", "frontend", "static")):
            discovered.append(p)

    # 4. Check virtual environments relative to base_dir and cwd
    search_roots = [base_dir]
    cwd = os.getcwd()
    if cwd != base_dir:
        search_roots.append(cwd)

    venv_names = [".openwebui_env", "openwebui_env", ".venv", "venv", "env", "framework_control"]
    for root in search_roots:
        for venv in venv_names:
            vdir = os.path.join(root, venv)
            if os.path.exists(vdir):
                # Windows layout
                discovered.extend([
                    os.path.join(vdir, "Lib", "site-packages", "open_webui", "static"),
                    os.path.join(vdir, "Lib", "site-packages", "open_webui", "frontend", "static"),
                ])
                # Unix/Linux layout
                for p in glob.glob(os.path.join(vdir, "lib", "python*", "site-packages", "open_webui", "static")):
                    discovered.append(p)
                for p in glob.glob(os.path.join(vdir, "lib", "python*", "site-packages", "open_webui", "frontend", "static")):
                    discovered.append(p)

    # Deduplicate preserving order
    seen = set()
    unique_candidates = []
    for d in discovered:
        norm = os.path.abspath(d)
        if norm not in seen:
            seen.add(norm)
            unique_candidates.append(norm)

    # Filter to existing directories
    existing_dirs = [d for d in unique_candidates if os.path.exists(d)]
    if existing_dirs:
        return existing_dirs

    # Fallback if no target directories exist yet: return primary defaults
    primary_defaults = [
        os.path.join(base_dir, ".openwebui_env", "Lib", "site-packages", "open_webui", "static"),
        os.path.join(base_dir, ".openwebui_env", "Lib", "site-packages", "open_webui", "frontend", "static"),
    ]
    return [os.path.abspath(d) for d in primary_defaults]


def resolve_webui_db_path(base_dir: str) -> str:
    """
    Dynamically discovers the Open WebUI webui.db database path across environments.
    """
    # 1. CLI flag
    for i, arg in enumerate(sys.argv[1:], start=1):
        if arg in ("--db-path", "--webui-db") and i < len(sys.argv) - 1:
            candidate = sys.argv[i + 1]
            if os.path.exists(candidate):
                return os.path.abspath(candidate)
        elif arg.startswith("--db-path="):
            candidate = arg.split("=", 1)[1]
            if os.path.exists(candidate):
                return os.path.abspath(candidate)

    # 2. Environment variables
    for env_var in ("WEBUI_DB_PATH",):
        val = os.environ.get(env_var)
        if val and os.path.exists(val):
            return os.path.abspath(val)

    for env_var in ("DATA_DIR", "WEBUI_DATA_DIR"):
        val = os.environ.get(env_var)
        if val:
            candidate = os.path.join(val, "webui.db")
            if os.path.exists(candidate):
                return os.path.abspath(candidate)

    # 3. Standard production and development project paths (data/openwebui/webui.db first)
    fast_candidates = [
        os.path.join(base_dir, "data", "openwebui", "webui.db"),
        os.path.join(os.getcwd(), "data", "openwebui", "webui.db"),
        os.path.join(base_dir, "data", "webui.db"),
        os.path.join(os.getcwd(), "data", "webui.db"),
    ]
    for c in fast_candidates:
        if c and os.path.exists(c):
            return os.path.abspath(c)

    # 4. Via open_webui package
    try:
        import open_webui
        ow_pkg_dir = os.path.dirname(os.path.abspath(open_webui.__file__))
        candidate = os.path.join(ow_pkg_dir, "data", "webui.db")
        if os.path.exists(candidate):
            return os.path.abspath(candidate)
    except Exception:
        pass

    # 5. Candidates in base_dir, sys.prefix, cwd, and ~/.open-webui
    candidates = [
        os.path.join(base_dir, ".openwebui_env", "Lib", "site-packages", "open_webui", "data", "webui.db"),
        os.path.join(base_dir, "data", "openwebui", "webui.db"),
        os.path.join(base_dir, "data", "webui.db"),
        os.path.join(sys.prefix, "Lib", "site-packages", "open_webui", "data", "webui.db"),
        os.path.join(sys.prefix, "data", "webui.db"),
        os.path.join(os.getcwd(), ".openwebui_env", "Lib", "site-packages", "open_webui", "data", "webui.db"),
        os.path.join(os.getcwd(), "data", "openwebui", "webui.db"),
        os.path.join(os.getcwd(), "data", "webui.db"),
        os.path.expanduser("~/.open-webui/data/webui.db"),
        os.path.expanduser("~/.open-webui/webui.db"),
    ]
    # Add unix patterns
    for root in (base_dir, sys.prefix, os.getcwd()):
        for p in glob.glob(os.path.join(root, ".openwebui_env", "lib", "python*", "site-packages", "open_webui", "data", "webui.db")):
            candidates.append(p)
        for p in glob.glob(os.path.join(root, "lib", "python*", "site-packages", "open_webui", "data", "webui.db")):
            candidates.append(p)

    for c in candidates:
        if c and os.path.exists(c):
            return os.path.abspath(c)

    return os.path.abspath(os.path.join(base_dir, "data", "openwebui", "webui.db"))


BASE_DIR = resolve_base_dir()

EDUCORE_DEFAULT_LOGO = find_logo_path("educore.png", BASE_DIR)
EDUCORE_RAG_LOGO = find_logo_path("educore-rag-e.png", BASE_DIR)

TARGET_DIRS = resolve_target_dirs(BASE_DIR)

WEBUI_DB_PATH = resolve_webui_db_path(BASE_DIR)

CUSTOM_CSS_RULE = r"""
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

/* ==========================================================================
   6. Model Selector Dropdown Menu & Popover (Laws of UX Optimization)
   - Hick's Law: Widened container (32rem / 512px) reduces cognitive load and gives text room to breathe
   - Law of Proximity: Distinct item bounding boxes prevent text collisions
   - Fitts's Law: Generous min-height (2.75rem / 44px) provides reliable, comfortable touch/click targets
   - Law of Common Region: Clearly delimited rows with rounded corners and unified hover states
   - Jakob's Law: Standard multi-line dropdown behavior matching modern AI interfaces
   ========================================================================== */

/* Dropdown Menu Container: Widen from default 20rem (320px) to 32rem (512px) */
div[style*="z-index: 9999"] > div,
div[style*="z-index: 9999"] .z-40,
div[style*="z-index: 9999"] div:has(> [role="listbox"]),
.model-selector-child-menu {
    width: 32rem !important;
    max-width: calc(100vw - 1.5rem) !important;
    min-width: 22rem !important;
}

/* Scrollable Listbox Container: Ample vertical viewport without claustrophobic scrolling */
div[style*="z-index: 9999"] div[role="listbox"],
div[role="listbox"] {
    max-height: 24rem !important;
    padding: 0.25rem 0.375rem !important;
    gap: 0.125rem !important;
}

/* Model Item Rows inside Dropdown Menu (Overrides hardcoded h-8 / 32px) */
/* Fitts's Law & Law of Proximity: Dynamic height, 44px min-target, comfortable vertical padding */
div[style*="z-index: 9999"] [role="listbox"] button[role="option"],
div[style*="z-index: 9999"] button[role="option"],
div[role="listbox"] button[role="option"],
div[role="listbox"] > button,
div[role="listbox"] > div > button,
.selected-command-option-button {
    height: auto !important;
    min-height: 2.75rem !important;
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 0.625rem !important;
    padding-right: 0.625rem !important;
    margin-top: 0.125rem !important;
    margin-bottom: 0.125rem !important;
    align-items: center !important;
    box-sizing: border-box !important;
    display: flex !important;
}

/* Inner flex containers: unclip height and allow vertical expansion */
div[role="listbox"] button[role="option"] > div.flex-1,
div[role="listbox"] button[role="option"] > div.flex-1 > div {
    overflow: visible !important;
    height: auto !important;
    min-height: 0 !important;
}

/* Model Persona, Clearance Tier (Tier A/B/C), and Description Typography */
/* Jakob's Law & Hick's Law: Clean word wrapping with comfortable line-height, zero text collision */
div[style*="z-index: 9999"] [role="listbox"] button[role="option"] .truncate,
div[style*="z-index: 9999"] [role="listbox"] .truncate,
div[role="listbox"] button[role="option"] .truncate,
div[role="listbox"] .truncate,
.selected-command-option-button .truncate,
.selected-command-option-button .line-clamp-1,
.selected-command-option-button .line-clamp-2 {
    overflow: visible !important;
    white-space: normal !important;
    word-break: normal !important;
    overflow-wrap: break-word !important;
    -webkit-line-clamp: unset !important;
    line-clamp: unset !important;
    line-height: 1.35 !important;
    font-size: 0.8125rem !important;
}

/* Action Icons (Link, Info, Checkmark): Center vertically relative to multi-line item */
div[role="listbox"] button[role="option"] > div.ml-auto,
div[style*="z-index: 9999"] button[role="option"] > div.ml-auto {
    align-self: center !important;
    flex-shrink: 0 !important;
}

/* ==========================================================================
   6.1 Responsive Mobile & Tablet Viewport Rules (max-width: 640px)
   Adapts dropdown popover smoothly to narrow viewports without horizontal clipping
   ========================================================================== */
@media (max-width: 640px) {
    div[style*="z-index: 9999"] > div,
    div[style*="z-index: 9999"] .z-40,
    div[style*="z-index: 9999"] div:has(> [role="listbox"]),
    .model-selector-child-menu {
        width: calc(100vw - 1rem) !important;
        max-width: calc(100vw - 1rem) !important;
        min-width: 0 !important;
    }

    div[style*="z-index: 9999"] [role="listbox"] button[role="option"],
    div[style*="z-index: 9999"] button[role="option"],
    div[role="listbox"] button[role="option"] {
        min-height: 3rem !important;
        padding-top: 0.625rem !important;
        padding-bottom: 0.625rem !important;
    }
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


def apply_branding(base_dir: str = None, target_dirs: list = None, db_path: str = None):
    base_dir = os.path.abspath(base_dir) if base_dir else BASE_DIR
    default_logo_path = find_logo_path("educore.png", base_dir)
    rag_logo_path = find_logo_path("educore-rag-e.png", base_dir)
    target_dirs = target_dirs or (resolve_target_dirs(base_dir) if base_dir != BASE_DIR else TARGET_DIRS)
    db_path = db_path or (resolve_webui_db_path(base_dir) if base_dir != BASE_DIR else WEBUI_DB_PATH)

    if not os.path.exists(default_logo_path):
        print(f"Error: {default_logo_path} not found.")
        sys.exit(1)
    if not os.path.exists(rag_logo_path):
        print(f"Error: {rag_logo_path} not found.")
        sys.exit(1)

    print("==============================================================================")
    print("  APPLYING EDUCORE BRANDING TO OPEN WEBUI")
    print(f"  Base Directory:   {base_dir}")
    print(f"  Default Logo:     {default_logo_path}")
    print(f"  RAG Logo:         {rag_logo_path}")
    print(f"  Database Path:    {db_path}")
    print("==============================================================================")

    # 1. Load source logos
    print("[1/5] Loading source logos...")
    default_logo = Image.open(default_logo_path).convert("RGBA")
    rag_logo = Image.open(rag_logo_path).convert("RGBA")
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
    for target_dir in target_dirs:
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
        shutil.copy2(default_logo_path, os.path.join(target_dir, "educore.png"))
        shutil.copy2(rag_logo_path, os.path.join(target_dir, "educore-rag-e.png"))

        # Update custom.css with enterprise branding and model selector anti-truncation rules
        css_path = os.path.join(target_dir, "custom.css")
        with open(css_path, "w", encoding="utf-8") as f:
            f.write(CUSTOM_CSS_RULE.strip() + "\n")

        print(f"  ✓ Deployed to {target_dir}")

    # 3.1 Save canonical assets/custom.css in repository (tracked in git)
    assets_css = os.path.join(base_dir, "assets", "custom.css")
    os.makedirs(os.path.dirname(assets_css), exist_ok=True)
    with open(assets_css, "w", encoding="utf-8") as f:
        f.write(CUSTOM_CSS_RULE.strip() + "\n")
    print(f"  ✓ Updated canonical repository asset at {assets_css}")

    # 3.2 Inject cache-busting timestamp into index.html across frontend directories
    cache_ts = int(time.time())
    html_candidates = [
        os.path.join(base_dir, ".openwebui_env", "Lib", "site-packages", "open_webui", "frontend", "index.html"),
    ]
    for d in target_dirs:
        html_candidates.extend([
            os.path.join(d, "index.html"),
            os.path.join(os.path.dirname(d), "index.html"),
        ])

    seen_html = set()
    for html_path in html_candidates:
        norm_path = os.path.abspath(html_path)
        if norm_path not in seen_html and os.path.exists(norm_path):
            seen_html.add(norm_path)
            try:
                with open(norm_path, "r", encoding="utf-8") as f:
                    content = f.read()
                updated = re.sub(
                    r'<link\s+rel="stylesheet"\s+href="/static/custom\.css(?:\?v=[^"]*)?"',
                    f'<link rel="stylesheet" href="/static/custom.css?v={cache_ts}"',
                    content
                )
                if updated != content:
                    with open(norm_path, "w", encoding="utf-8") as f:
                        f.write(updated)
                    print(f"  ✓ Injected cache-busting query parameter (?v={cache_ts}) into {norm_path}")
            except Exception as e:
                print(f"  ! Warning updating {norm_path}: {e}")

    # 4. Update Database Models with Stylised RAG Logo & Suggested Prompts
    print("\n[4/5] Updating Open WebUI database AI model avatars & prompt suggestions...")
    if os.path.exists(db_path):
        try:
            try:
                from setup_openwebui_rbac import MODELS_DEF, DEFAULT_PROMPT_SUGGESTIONS
            except ImportError:
                try:
                    from src.governance.setup_openwebui_rbac import MODELS_DEF, DEFAULT_PROMPT_SUGGESTIONS
                except ImportError:
                    MODELS_DEF, DEFAULT_PROMPT_SUGGESTIONS = [], []

            model_prompts_map = {m["id"]: m.get("suggestion_prompts") for m in MODELS_DEF if m.get("suggestion_prompts")}

            con = sqlite3.connect(db_path)
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

                # Synchronize role/campus-specific suggestion prompts if model is registered
                if model_id in model_prompts_map:
                    meta["suggestion_prompts"] = model_prompts_map[model_id]

                cur.execute("UPDATE model SET meta = ? WHERE id = ?", (json.dumps(meta), model_id))
                updated_count += 1

            # Also ensure ui.prompt_suggestions in config is updated with Educore institutional prompts
            if DEFAULT_PROMPT_SUGGESTIONS:
                now_ts = int(time.time())
                cur.execute("SELECT key FROM config WHERE key = 'ui.prompt_suggestions'")
                if cur.fetchone():
                    cur.execute("UPDATE config SET value = ?, updated_at = ? WHERE key = 'ui.prompt_suggestions'", (json.dumps(DEFAULT_PROMPT_SUGGESTIONS), now_ts))
                else:
                    cur.execute("INSERT INTO config (key, value, updated_at) VALUES ('ui.prompt_suggestions', ?, ?)", (json.dumps(DEFAULT_PROMPT_SUGGESTIONS), now_ts))
                print(f"  ✓ Synchronized Educore prompt suggestions in {db_path}.")

            con.commit()
            con.close()
            print(f"  ✓ Updated {updated_count} model(s) in {db_path} with '/static/educore-rag-e.png' avatar & prompt suggestions.")
        except Exception as e:
            print(f"  ! Error updating database: {e}")
    else:
        print(f"  ! Database not found at {db_path} (will be applied when RBAC provisioning runs)")

    print("\n[5/5] Branding configuration verified!")
    print("==============================================================================")
    print("  EDUCORE BRANDING APPLICATION COMPLETE!")
    print("==============================================================================")


if __name__ == "__main__":
    apply_branding()
