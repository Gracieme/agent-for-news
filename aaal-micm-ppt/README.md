# MICM AAAL 2026 Presentation

Conference presentation for **AAAL 2026** based on *MICM_Final_v5.pdf*:  
**Translanguaging as Mediational Architecture: Reconceptualizing Negotiation, Reflection, and Interactional Competence in CSL Peer Interaction**

## File

- **MICM_AAAL2026.pptx** — 21 slides, 16:9. Open in PowerPoint, Keynote, or Google Slides.
- **Slide transitions**: Fade (medium speed) applied to all slides via OOXML post-process. Run the build script to regenerate with transitions.

## Design (AAAL Inclusive Presenter Guidelines)

- **Font**: Arial (sans-serif). Title 40pt, section titles 32pt, body 24pt.
- **Colors**: Off-white background (#F4F6F6), charcoal text (#2C2C2C), teal accent (#277884). No red/green or other combinations that fail accessibility.
- **Layout**: One main idea per slide; bullets kept to 1–2 lines; content in upper/middle of slide (no critical text at bottom).
- **Tables**: LRE type distribution, NoM strategy distribution, NoM→LRE transition rates on separate slides; font size 24pt for readability.

## Regenerating

```bash
pip install python-pptx   # or: python3 -m pip install python-pptx
python3 build_micm_aaal_ppt.py
```

## Before Presenting (AAAL checklist)

1. Run your software’s **accessibility checker** (e.g. PowerPoint: Review → Check Accessibility).
2. If you share slides in advance (e.g. for interpreters or blind/visually impaired participants), use the same .pptx or an exported PDF and ensure **alt text** is added to any images (this deck is text/tables only).
3. Consider **live captioning** (PowerPoint: Slide Show → Always Use Subtitles; [AAAL guidelines](https://www.aaal.org/inclusive-presenter-guidelines)).
4. Use the **microphone** and a **moderate pace**; repeat audience questions before answering.
