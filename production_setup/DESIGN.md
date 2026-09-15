# EduCore Enterprise RAG - Design System Specification (DESIGN.md)

## Design Direction: "Enterprise Obsidian & Aurora"
An ultra-refined, high-density workstation aesthetic tailored for security-conscious enterprise operators, educators, and institutional leadership. Moves decisively away from generic boxy gray dashboards into an authoritative, tactile, luminous dark-mode environment.

## Design Mode
- **Mode:** `Operate`
- **Focus:** Scanability, information density, crisp typography, intuitive role switching, instant telemetry visibility, zero visual friction.

## Color Tokens & Atmosphere
- **Canvas Base:** Deep Obsidian `#070A10`
- **Surface Elevation 1 (Card/Panel):** Frosted Glass `#0E1422` with 75% opacity and `backdrop-filter: blur(16px)`
- **Surface Elevation 2 (Elevated/Hover):** `#162035`
- **Surface Elevation 3 (Active/Inset):** `#1C2942`
- **Borders & Dividers:**
  - Subtle Border: `rgba(255, 255, 255, 0.07)`
  - Active/Focus Border: `rgba(59, 130, 246, 0.55)`
  - Card Highlight Line: `linear-gradient(90deg, rgba(59, 130, 246, 0.3) 0%, rgba(139, 92, 246, 0) 100%)`
- **Brand Accents & Gradients:**
  - Primary Aurora: `linear-gradient(135deg, #3B82F6 0%, #6366F1 50%, #8B5CF6 100%)`
  - Emerald Safety (Permitted / Pass): `#10B981` (Glow: `rgba(16, 185, 129, 0.25)`)
  - Amber Warning (Staff / Review): `#F59E0B` (Glow: `rgba(245, 158, 11, 0.25)`)
  - Violet Confidential (Counselor / Case #402): `#8B5CF6` (Glow: `rgba(139, 92, 246, 0.25)`)
  - Crimson Restrict (Access Denied / Leakage): `#EF4444` (Glow: `rgba(239, 68, 68, 0.25)`)
  - Cyan Informational (Public / Syllabus): `#06B6D4` (Glow: `rgba(6, 182, 212, 0.25)`)

## Typography & Hierarchy
- **Primary Body & UI:** `'Plus Jakarta Sans'`, `'Inter'`, system-ui, sans-serif
- **Monospace & Code:** `'JetBrains Mono'`, `'Fira Code'`, monospace
- **Scale:**
  - Display Title: 24px, 700 weight, letter-spacing: -0.03em, gradient clip
  - Section Title: 16px, 600 weight, letter-spacing: -0.02em
  - Card Label: 11px, 600 weight, text-transform: uppercase, letter-spacing: 0.08em
  - Body Text: 14px, 400/500 weight, line-height: 1.6
  - Micro / Telemetry: 12px, tabular numbers, font-family: monospace

## Component Specifications
1. **Security Command Bar (Header):**
   - Brand logo with iridescent aurora glow.
   - ISO 42001 Live Compliance Pulse: green pulsating orb showing active zero-trust guardrails.
   - Quick Persona Switcher: drop-in identity chips permitting instant evaluation without logging out.
   - Navigation Segmented Tabs with sliding pill active indicators.
   - Active User Badge with avatar initials, role clearance, and campus tag.

2. **Authentication Gateway (Login):**
   - Holographic Identity Cards: 4 distinct security clearance badges with hover elevation, clearance crests, authorized data scopes, and single-click access.
   - Credentials input dock with sleek outline focus, clear error messaging, and demo helper hints.

3. **AI Chat Studio (Conversational RAG):**
   - Full-height flex workstation layout.
   - Embedded lightweight Markdown Parser: renders markdown headers, bold/italics, bulleted lists, numbered lists, blockquotes, tables, and styled code blocks.
   - Message Utility Footer: copy answer button with animated "Copied!" checkmark, latency indicator, and citation chips.
   - Query Suggestion Chips: interactive chips with hover lift and category pills.
   - Live Telemetry HUD: visual metrics for latency, chunk counts, access decision, and PII egress shield.
   - Context Inspector Drawer: interactive cards displaying retrieved document chunks with similarity distance and source metadata.

4. **Role Tool Suites:**
   - Interactive search and filter bars.
   - High-contrast data tables with zebra hover and monospace identifiers.
   - Modern accordion panels and metric cards.
   - Responsive layout adapting smoothly to desktop and mobile screens.
