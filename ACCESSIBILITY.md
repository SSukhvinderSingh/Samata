# Samata — Accessibility (a11y) & WCAG 2.1 AA Compliance ♿

## 1. Accessibility Statement
**Samata** is engineered to be universally accessible, adhering strictly to **Web Content Accessibility Guidelines (WCAG) 2.1 Level AA** standards. Legal empowerment must be inclusive of all citizens, including individuals with visual impairments, motor constraints, low digital literacy, and linguistic diversity.

---

## 2. WCAG 2.1 AA Compliance Checklist

| WCAG Principle | Guideline & Success Criterion | Implementation in Samata | Compliance Level |
| :--- | :--- | :--- | :---: |
| **1. Perceivable** | 1.4.3 Contrast (Minimum) | Text and interactive elements maintain a contrast ratio &ge; **4.5:1** against backgrounds in both Dark and Light modes. | **Level AA** ✅ |
| **1. Perceivable** | 1.4.12 Text Spacing | Responsive typography using variable scaling (`rem`/`em`) and adjustable font sizing (Normal, Large, Extra Large). | **Level AA** ✅ |
| **2. Operable** | 2.1.1 Keyboard Navigation | 100% of interactive controls (agent selection, quick starters, text inputs, feedback rating) are keyboard reachable via `Tab` and executable via `Enter`/`Space`. | **Level AA** ✅ |
| **2. Operable** | 2.4.7 Focus Visible | High-visibility active focus rings (`#06b6d4` Electric Cyan and `#d97706` Amber Gold) indicate active focus state. | **Level AA** ✅ |
| **2. Operable** | 2.5.5 Target Size | Interactive chips, buttons, and autocomplete triggers feature a minimum touch target size of **44x44 CSS pixels**. | **Level AA** ✅ |
| **3. Understandable** | 3.1.2 Language of Parts | Vernacular Hinglish mode (`@simplify`) allows code-switched legal queries for citizens comfortable in spoken Hindi-English. | **Level AA** ✅ |
| **3. Understandable** | 3.3.1 Error Identification | Input validation failures and network retries provide descriptive, human-readable feedback. | **Level AA** ✅ |
| **4. Robust** | 4.1.2 Name, Role, Value | Semantic HTML5 tags (`<header>`, `<main>`, `<section>`, `<nav>`) and ARIA labels for assistive technologies. | **Level AA** ✅ |

---

## 3. Assistive Technology & Multi-Modal Access

### Screen Reader Optimization
- Dynamic message containers announce status updates to screen readers (`NVDA`, `JAWS`, `VoiceOver`).
- Collapsible verification dockets and citation badges include descriptive `aria-expanded` and `aria-label` tags.

### Cognitive & Plain-Language Inclusivity
- **The Simplifier Agent (`@simplify`)**: Eliminates Latin legal phrases (e.g. *pendente lite*, *ex-parte*, *restitutio in integrum*) and translates them into everyday conversational language.
- **Hinglish Mode**: Provides colloquial explanations tailored for non-fluent English speakers across India.

### Emergency Crisis Accessibility
- Prominently visible and screen-reader prioritized crisis alert banners for domestic violence, mental health, and child distress.
