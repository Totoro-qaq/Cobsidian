# Cobsidian V2 Motion Spec — Vault Proof

This is the design specification for the next production GIF. It replaces the
transaction-ledger presentation with a user-visible Obsidian knowledge loop.

## Story

The animation follows one piece of knowledge all the way through the vault:

1. Open the actual Obsidian vault and focus an existing note.
2. Match filename, H1, frontmatter title, and aliases to that canonical note.
3. Show a readable note diff and let the user apply the reviewed patch.
4. Write atomically, validate the note, and keep rollback available.
5. Switch to Graph view and reveal the new backlinks as a colorful knowledge
   pulse around the updated note.

The public animation never displays raw JSON or a plan ID. The deterministic
writer still binds confirmation to the exact patch internally, and the full ID
remains available in the CLI, manifest, and transaction record.

All public titles and paths are synthetic. The canonical example is
`RAG Pipeline.md`; the Chinese alias `检索增强生成` demonstrates multilingual
identity matching while all interface instructions remain English-first.

## Timing

| Label | Time | Visual action |
|---|---:|---|
| `vault` | 0.0s | The Obsidian vault opens with `RAG Pipeline.md` already visible. |
| `match` | 1.1s | Identity candidates resolve into the existing note; `Append` becomes the decision. |
| `review` | 2.7s | Human-readable remove/add rows appear inside the Obsidian context. |
| `apply` | 4.5s | `Apply reviewed patch` is activated and the note receives the new paragraph and wikilinks. |
| `validate` | 5.7s | `Saved · Validated · Rollback ready` becomes visible. |
| `graph` | 6.2s | The editor transitions to a light Graph view; the updated note remains the visual anchor. |
| `connect-primary` | 6.8–8.8s | Four primary edges grow outward one by one, followed by their topic-colored nodes. |
| `connect-secondary` | 8.8–10.9s | Supporting paths and outer nodes complete the local knowledge neighborhood. |
| `hold` | 10.9–12.8s | The connected graph remains readable before a short crossfade restarts the loop. |

## Motion Implementation Contract

The self-contained recorder page uses equivalent deterministic CSS keyframes so
the README asset has no runtime dependency. Interactive product implementations
should use the GSAP timeline contract below.

- Build one `gsap.timeline()` with named labels and shared defaults:
  `duration: 0.48`, `ease: "power3.out"`.
- Use timeline position parameters instead of per-element `delay` values.
- Use `autoAlpha`, `x`, `y`, and `scale`; do not animate layout properties.
- Keep the note visible while the decision and review layers resolve so the user
  never loses Obsidian context.
- Draw graph edges with `strokeDasharray` and `strokeDashoffset`, using
  `ease: "power2.inOut"`. Resolve linked nodes with a restrained scale from
  `0.92` to `1`; no bounce, elastic motion, or random orbiting.
- Treat color as information: violet for the canonical note, cyan for search,
  amber for embeddings, rose for evaluation, green for agent workflows, and blue
  for supporting concepts.
- Keep the entire surface light: neutral editor, pale sidebar, and off-white Graph
  view. Do not use a dark terminal or dark graph canvas.
- The graph animation is one extended outward knowledge pulse, not perpetual
  ambient drift. Its growth phase lasts roughly four seconds before the final hold.
- Use `gsap.matchMedia()` for `(prefers-reduced-motion: reduce)`. Reduced motion
  crossfades directly from the written note to the completed graph and does not
  loop.
- The non-animated HTML/SVG default must remain fully visible so paused tabs and
  headless renderers never capture a blank asset.
- Production recording must use a locally installed or vendored GSAP build; the
  README asset must not depend on a CDN or network request.

## Recording

- Artboard: `1280 × 720`.
- Output: native `1280 × 720`, 8–10 effective frames per second after optimization.
- Target duration: `12.8s` plus a clean crossfade loop cut.
- Target file size: below `4 MB`; Graph view labels and edge clarity take priority
  over aggressive palette reduction.
- Preserve the completed graph as the static final frame for users who do not
  autoplay GIFs.
