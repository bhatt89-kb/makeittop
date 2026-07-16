# Accessibility

StadiumOS GenAI targets **WCAG 2.1 Level AA** across the console. This document lists what's implemented
and how to manually verify it — accessibility conformance is only as real as it is testable.

## 1. Implemented

- **Skip link** — first focusable element on the page (`Skip to main content`), jumps past the ticker and
  header nav straight to the module panel.
- **Semantic landmarks** — `<header>`, `<nav>`, `<main>`, `<footer>`, with `role="tablist"` /
  `role="tab"` / `role="tabpanel"` correctly wired via `aria-controls` / `aria-selected` / `aria-labelledby`
  for the module switcher.
- **Full keyboard operability** — the module rail supports Arrow Up/Down/Left/Right, Home, and End per the
  WAI-ARIA Tabs Pattern, in addition to standard Tab/Shift+Tab and Enter/Space activation on every
  button, link, and form control. No mouse-only interaction exists anywhere in the app.
- **Visible focus indicators** — a 3px gold focus ring (`:focus-visible`) on every interactive element,
  including in high-contrast mode, meeting the WCAG 2.4.7 (Focus Visible) success criterion.
- **`aria-live` regions** — chat replies, navigation results, crowd alerts, accessibility guidance,
  sustainability tips, and emergency instructions are all announced to screen-reader users as they arrive
  asynchronously (`aria-live="polite"` for informational results, `aria-live="assertive"` for emergency
  guidance, matching its urgency).
- **Labelled form controls** — every `<input>`/`<select>` has a programmatically associated `<label>`;
  icon-only or visually-implied controls carry `aria-label` (e.g. the "✕ remove zone" button).
- **High-contrast mode toggle** — swaps the palette to pure black/white/high-luminance gold, exceeding a
  7:1 contrast ratio for body text (WCAG AAA-level contrast, opt-in) while remaining a normal-contrast
  design by default that already meets AA (4.5:1 body text, 3:1 large text/UI components).
- **Adjustable text size** — a three-step toggle (normal / large / x-large) that scales the base font size
  via a single CSS custom property, so layout reflows correctly without horizontal scrolling (WCAG 1.4.4
  Resize Text).
- **`prefers-reduced-motion` respected** — the header ticker's scrolling animation and all transitions are
  disabled for users who have requested reduced motion at the OS level (WCAG 2.3.3).
- **No colour-only signaling** — crowd severity and route accessibility are conveyed with both colour *and*
  text labels (`data-severity="critical"` + the word "CRITICAL" in the alert meta line; a step-free route
  is labelled "♿ Step-free route" in text, not just an icon).
- **Responsive down to narrow viewports** — the module rail collapses to a horizontal scrollable strip
  below 820px width rather than being clipped or hidden.
- **Plain-language content** — copy is written in short, active-voice sentences (see the `frontend-design`
  writing guidance this project follows); the emergency panel explicitly states its own limitation
  ("Not a replacement for emergency services") in the interface's voice, not a legal disclaimer wall.

## 2. Manual verification checklist

Run through this before any release:

1. Unplug your mouse. Tab from the top of the page to the bottom — confirm every interactive element is
   reachable, in a logical order, with a visible focus ring at every stop.
2. On the module rail, focus the first tab and use Arrow Down/Up — confirm focus (and the visible panel)
   moves correctly, and Home/End jump to the first/last tab.
3. Turn on a screen reader (VoiceOver / NVDA) and submit the chat form — confirm the reply is announced
   without needing to manually navigate to it.
4. Toggle "High contrast" and "Large text" — confirm no text is clipped or overlapping at the largest size.
5. Enable "reduce motion" at the OS level, reload — confirm the ticker no longer scrolls.
6. Resize the browser to 375px wide — confirm the module rail becomes a horizontal strip and no content
   is cut off.

## 3. Known gaps (tracked in `docs/UNFINISHED.md`)

- No automated accessibility test (e.g. `axe-core`) is wired into CI yet — manual checklist only for now.
- Colour contrast has been checked by design token construction, not yet run through an automated
  contrast-ratio tool against every state (e.g. the amber "medium" alert on the dark green card).
- Screen-reader testing has been done conceptually against ARIA best practices, not yet validated against
  a real screen reader by a person with lived accessibility expertise — this is the single highest-value
  next step before any real deployment.
