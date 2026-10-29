---
name: ecc-a11y-audit
description: >-
  WCAG 2.2 Level AA accessibility auditing and testing workflow. Covers
  audit checklists, automated scanning tools (axe-core, Lighthouse, Pa11y),
  manual testing protocols, screen reader testing, keyboard navigation
  testing, color contrast verification, and mobile accessibility (MASVS).
  Use for accessibility audits, compliance checks, a11y test planning, or
  when verifying WCAG conformance. For implementation patterns (ARIA,
  semantic HTML, component code), use the `accessibility` and
  `frontend-a11y` skills instead. Triggers: "accessibility audit", "a11y
  audit", "WCAG compliance", "accessibility test", "screen reader test",
  "keyboard test", "color contrast check", "Section 508 audit", "ADA
  compliance check".
---

# ecc-a11y-audit

## When to Use

- Auditing a web or mobile app for WCAG 2.2 Level AA compliance
- Planning an accessibility testing sprint
- Running automated accessibility scans (axe-core, Lighthouse, Pa11y)
- Conducting manual accessibility testing (keyboard, screen reader, contrast)
- Verifying accessibility compliance before deployment
- Creating accessibility test plans and evidence reports

## When NOT to Use (Use These Instead)

- **Implementing ARIA patterns or semantic HTML** -> use `accessibility` skill
- **Building accessible React/Next.js components** -> use `frontend-a11y` skill
- **Designing accessible UI components** -> use `design-system` skill

## WCAG 2.2 Level AA Quick Reference

### Perceivable

| Criterion | ID | What to Check |
|-----------|-----|---------------|
| Non-text Contrast | 1.4.11 | UI components and graphics have 3:1 contrast minimum |
| Text Spacing | 1.4.12 | Text remains readable when spacing is overridden |
| Content on Hover or Focus | 1.4.13 | Hover/focus content is dismissable, hoverable, and persistent |
| Identify Input Purpose | 1.3.5 | Input fields use correct `autocomplete` attributes |
| Identify Purpose | 1.3.6 | Purpose of UI components can be programmatically determined |

### Operable

| Criterion | ID | What to Check |
|-----------|-----|---------------|
| Keyboard | 2.1.1 | All functionality is operable from keyboard |
| No Keyboard Trap | 2.1.2 | Focus can move away from any component via keyboard |
| Pointer Cancellation | 2.5.4 | Pointer input can be cancelled or aborted |
| Target Size (Minimum) | 2.5.8 | Touch targets are at least 24×24 CSS pixels |
| Focus Not Obscured | 2.4.11 | Focused element is not entirely hidden by sticky headers/footers |
| Focus Appearance | 2.4.12 | Focus indicator has sufficient size and contrast |

### Understandable

| Criterion | ID | What to Check |
|-----------|-----|---------------|
| Consistent Help | 3.2.6 | Help mechanisms are in the same relative order across pages |
| Redundant Entry | 3.3.7 | Previously entered info is auto-populated or available |
| Accessible Authentication | 3.3.8 | No cognitive function test for authentication |

### Robust

| Criterion | ID | What to Check |
|-----------|-----|---------------|
| Status Messages | 4.1.3 | Status messages use `role="status"` or `aria-live` |

## Audit Checklist by Category

### Keyboard Navigation Audit

| Component | Key | Expected Action | Pass/Fail |
|----------|-----|-----------------|-----------|
| Tabs | Arrow Left/Right | Move between tabs | |
| Tabs | Home/End | First/last tab | |
| Dialog | Escape | Close dialog, return focus to trigger | |
| Menu | Arrow Up/Down | Navigate menu items | |
| Menu | Escape | Close menu, return focus | |
| Combobox | Arrow Down | Open dropdown, move to first option | |
| Treeview | Arrow Up/Down | Move between tree nodes | |
| Treeview | Arrow Right | Expand node or move to child | |
| Treeview | Arrow Left | Collapse node or move to parent | |

### Focus Management Audit

- [ ] Focus moves to dialog when opened
- [ ] Focus is trapped within dialog while open
- [ ] Focus returns to trigger element when dialog closes
- [ ] Skip-to-content link is the first focusable element
- [ ] Focus indicator is visible (minimum 2px outline, 3:1 contrast)
- [ ] No keyboard traps — Tab and Shift+Tab work everywhere
- [ ] `tabindex="-1"` for non-focusable elements that need programmatic focus
- [ ] `tabindex="0"` for custom interactive elements that need keyboard access

### Color Contrast Requirements

| Element | Normal Text | Large Text (18pt+/14pt bold) | UI Components |
|---------|-------------|------------------------------|---------------|
| Minimum (AA) | 4.5:1 | 3:1 | 3:1 |
| Enhanced (AAA) | 7:1 | 4.5:1 | — |

### Common Contrast Failures

- Placeholder text below 4.5:1 contrast
- Disabled button states below 3:1 contrast
- Link text indistinguishable from surrounding body text
- Focus indicators below 3:1 contrast against background
- Icon-only buttons without `aria-label` and sufficient contrast

## Testing Workflow

### 1. Automated Testing

```bash
# axe-core (browser extension or CLI)
npx @axe-core/cli http://localhost:3000 --tags wcag2aa

# Lighthouse CI
npx lighthouse http://localhost:3000 --only-categories=accessibility

# Pa11y CLI
npx pa11y http://localhost:3000 --standard WCAG2AA

# Playwright with axe
npx playwright test --grep "accessibility"
```

### 2. Manual Testing Checklist

- [ ] Navigate entire page with Tab/Shift+Tab — verify logical focus order
- [ ] Test all interactive elements with keyboard only
- [ ] Test with screen reader (NVDA/VoiceOver) — verify page structure announced
- [ ] Verify all images have `alt` text (decorative images use `alt=""`)
- [ ] Check color contrast with browser DevTools
- [ ] Test at 200% zoom — no horizontal scrolling, no lost functionality
- [ ] Test with high contrast mode — all content visible
- [ ] Verify form error messages are announced via `aria-live`
- [ ] Test skip-to-content link functionality
- [ ] Verify all video has captions, audio has transcripts

### 3. Screen Reader Testing

**NVDA (Windows, free):**
- Navigate with `Insert+Down Arrow` to read page
- Use `H` to jump between headings
- Use `K` to jump between links
- Use `F` to jump between form fields
- Use `T` to jump between tables

**VoiceOver (macOS, built-in):**
- `Cmd+F5` to toggle VoiceOver
- `Ctrl+Option+Down Arrow` to read page
- `Ctrl+Option+Cmd+H` to jump between headings
- `Ctrl+Option+Right Arrow` to navigate elements

## Mobile Accessibility (MASVS v2.1.0)

- Touch targets minimum 44×44 pt (iOS) / 48×48 dp (Android)
- Support dynamic type / font scaling
- Maintain accessibility labels on custom UI components
- Test with TalkBack (Android) and VoiceOver (iOS)
- Verify pinch-to-zoom is not disabled unless essential

## Integration

- **Router**: `frontend-skills` and `accessibility` domain routers
- **Implementation**: Use `accessibility` for ARIA/semantic HTML patterns, `frontend-a11y` for React/Next.js component patterns
- **Testing**: Use with `e2e-testing` (Playwright) for automated a11y tests
- **Security**: Accessible auth patterns align with `ecc-owasp-security` (ASVS V2.1)
- **Verification**: Use `ecc-verify` to gate deployment on accessibility compliance

## Auto-Revocation

This skill has **no external tool dependencies**. All audit patterns are
markdown guidance and checklists.

- **Core tools** (never gate): `grep`, `cat`, `head` — used for HTML/ARIA review
- **Advisory tools**: `axe-core`, `lighthouse`, `pa11y`, `playwright` — if
  available, use for automated scanning; if absent, fall back to manual checklist
- Wrap automated tool calls with `2>/dev/null` and `|| true`

## Cross-IDE Compatibility

Pure markdown skill — no runtime dependencies:
- **Windsurf**: SKILL.md auto-discovered
- **Devin**: SKILL.md injected as context
- **Autogravity**: SKILL.md read as agent capability
- **Codex**: `agents/openai.yaml` provides agent definition

## Upstream Source

Adapted from [aitmpl.com](https://www.aitmpl.com/) accessibility agent component and WCAG 2.2 specification (W3C). Narrowed to audit/testing scope; implementation patterns deferred to existing `accessibility` and `frontend-a11y` skills.
