# Design

> Source of truth for Cobsidian visual assets: README banner, demo previews, and future recording-safe marketing material.
> Read this before touching visual UI assets.

## Aesthetic Direction

Light Codex-like workbench: warm neutral surface, restrained glass panels, small violet wiki-link accents, and knowledge-vault semantics without vendor logos.

## Dials

- DESIGN_VARIANCE: 8 / 10
- MOTION_INTENSITY: 6 / 10
- VISUAL_DENSITY: 4 / 10

## Type Stack

- Display: Aptos Display, SF Pro Display, or Segoe UI Variable Display fallback. Then Helvetica Neue, sans-serif.
- Body: Aptos, SF Pro, or Segoe UI Variable fallback. Then Helvetica Neue, sans-serif.
- Mono: Cascadia Code, JetBrains Mono, or Consolas fallback.
- Banned: Inter, Roboto, Arial, generic `system-ui` as primary.

## Color Tokens

```css
:root {
  --neutral-surface: oklch(0.98 0.008 85);
  --bg: oklch(0.96 0.012 90);
  --bg-deep: oklch(0.91 0.018 250);
  --surface: oklch(1 0 0 / 0.76);
  --fg: oklch(0.23 0.025 260);
  --muted: oklch(0.48 0.035 255);
  --accent-violet: oklch(0.56 0.16 292);
  --accent-teal: oklch(0.58 0.11 180);
  --accent: var(--accent-violet);
  --border: oklch(0.70 0.035 250 / 0.34);
}
```

Banned:

- Purple-to-blue gradients on white.
- Pure black or pure white as primary background/text.
- External image or font dependencies for README/demo assets.
- Official Obsidian, OpenAI, Codex, Claude, Cursor, or other vendor logos in Cobsidian visuals.

Use abstract note-link diagrams with concrete note titles (e.g., three connected note cards showing "RAG", "Agents", "Vector DB") to illustrate the linking concept. Avoid empty bracket-only icons like `[[ ]]` in isolation — they read as placeholders rather than meaningful symbols. Do not use crystal marks or modified vendor icons.

## Motion

- CSS-only motion for portable demo assets.
- Default easing: `cubic-bezier(0.16, 1, 0.3, 1)`.
- Animate only `transform` and `opacity`.
- Respect `prefers-reduced-motion`.

## Layout

- Recording demos use a 1280x720 fixed artboard.
- README banner uses a 1200x360 SVG artboard.
- Use split-screen operational layouts: terminal or dry-run plan on the left, note/vault preview on the right.
- Keep all demo content synthetic. Never use a private vault path, private note title, API key, token, or screenshot from a real workspace.

## Last Updated

2026-07-08: Replaced abstract [[ ]] marks with concrete knowledge-graph nodes in banner and demo. Added macOS font fallbacks. Improved demo content to show real knowledge notes instead of product meta-descriptions.
2026-07-07: Added recording-safe pseudo-terminal and Obsidian note demo direction.
2026-07-07: Removed the prior purple-crystal direction because it could be confused with vendor iconography.
2026-07-07: Reworked visual assets to a light Codex-like workbench and removed crystal marks.
