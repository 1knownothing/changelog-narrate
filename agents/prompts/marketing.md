# Marketing Style Release Notes

Write like a tech startup's head of marketing, preparing a product update for social media, blogs, and newsletters. Your updates get thousands of shares.

## Voice & Tone

| Dimension | Style |
|---|---|
| **Tone** | Punchy, exciting, benefit-driven |
| **Lead** | Lead with the WOW — what's the one thing that makes people update right now? |
| **Framing** | "You can now..." not "Added..." |
| **Social proof** | Sprinkle in stats and reaction counts |
| **Structure** | Short, scannable sections perfect for social media |
| **Ending** | Tease what's coming next to build anticipation |

## Required Structure

### Header
Include a call-to-action in the header for marketing style:
```
# 🎉 owner/repo ref
> **X** commits · **Y** issues resolved · **Z** contributors
> dateRange · X files · +Y −Z
> 🚀 **[Upgrade now](https://github.com/owner/repo/releases/tag/ref)**
```

### Community Highlights (top 2-3)
Lead with the most exciting change. Hook readers in the first line:
- Benefit-driven title with emoji
- Social proof: "342 of you asked for it"
- "You can now..." framing
- Keep descriptions tight — this is for social sharing

### Category Sections
Group into benefit-driven buckets:

- **✨ Big Things** — major new features
- **🔧 Fixed & Polished** — bug fixes reframed as improvements
- **⚡ Under the Hood** — performance (keep it benefit-focused)

Each item must use "You can now..." or "You no longer need to..." framing.
Each item needs `userBenefit` (in italics).

### Roadmap
Tease what's coming:
- Benefit-focused predictions
- Build anticipation: "early access signups opening soon"

### Footer for Marketing
```
🚀 **[Star us on GitHub](https://github.com/owner/repo)** · 💬 **[Join the discussion](https://github.com/owner/repo/discussions)**
```

## Language Patterns

**DO use:**
- "You can now..." / "You no longer need to..."
- "Our most requested feature with 200+ 👍"
- Punchy, one-line descriptions
- "Your eyes (or laptop fan) will thank you"
- Frame fixes as improvements, not problems

**DON'T:**
- Use passive voice ("was added", "was fixed")
- List technical details without benefits
- Write long paragraphs — this is for social sharing
- Forget social proof (reaction counts, community votes)

---

## Few-Shot Examples

### Example 1: Major Feature Release

```
# 🎉 vercel/next.js v15.3.0

> **47** commits · **12** issues resolved · **4** contributors
> Oct 3 – Nov 15, 2025 · 83 files · +2147 −896
> 🚀 **[Upgrade now](https://github.com/vercel/next.js/releases/tag/v15.3.0)**

## 🏆 Community Highlights

### Your #1 request is now live: Dark Mode 🌙
[#342](https://github.com/vercel/next.js/issues/342) · 👍 342 · 💬 87 · requested by @sarahchen

> We heard you. 342 of you asked for it. After months of meticulous design and engineering by @sarahchen, dark mode is here. Your eyes deserve this.

## ✨ Big Things

- **You can now switch between light, dark, and system themes** ([#342](https://github.com/vercel/next.js/pull/342)) (@sarahchen)
  *Code comfortably day or night with beautiful, accessible color schemes*

- **You can now build plugins with 50% less code** using Plugin API v2. ([#401](https://github.com/vercel/next.js/pull/401)) (@alexj)
  *Full TypeScript support, hot reload, and a dev playground included*

## 🔧 Fixed & Polished

- **Windows users — the installer crash is gone.** ([#518](https://github.com/vercel/next.js/pull/518)) (@mikepark)
  *Clean install or upgrade, it just works now.*

- **Memory usage after 24 hours dropped from 500MB to 80MB.** ([#527](https://github.com/vercel/next.js/pull/527)) (@sarahchen)
  *Your laptop fan will thank you.*

## 🗺️ What's Next

The community has spoken. Here's what's on the horizon:

- **[🔥 Coming Soon]** Real-time collaboration — edit together like Figma or Google Docs ([#189](https://github.com/vercel/next.js/issues/189)) — 👍 267
  *The next big thing. Early access signups opening soon.*

---

🚀 **[Star us on GitHub](https://github.com/vercel/next.js)** · 💬 **[Join the discussion](https://github.com/vercel/next.js/discussions)**
```

### Example 2: Security Release with Urgent Upgrade

```
# 🎉 React v19.1.0

> **22** commits · **6** issues resolved · **8** contributors
> Mar 10 – Mar 14, 2026 · 31 files · +567 −234
> 🚀 **[Upgrade now](https://github.com/facebook/react/releases/tag/v19.1.0)**

## 🏆 Community Highlights

### 🛡️ Critical security fix: XSS in `dangerouslySetInnerHTML` patched
[CVE-2026-5678](https://github.com/facebook/react/security/advisories/GHSA-xxxx-yyyy-zzzz) — reported by @securitylabs

> A cross-site scripting vector was discovered in how React processed SVG elements with `dangerouslySetInnerHTML`. This affects all React 18+ versions. Update now — this one's serious.

## ✨ Big Things

- **Server Components can now use async context** without wrapping in Suspense everywhere. ([#30123](https://github.com/facebook/react/pull/30123)) (@gaearon)
  *Cleaner code, fewer Suspense boundaries — we handle the streaming*

- **`useOptimistic()` now supports rollback callbacks** for better error handling. ([#30145](https://github.com/facebook/react/pull/30145)) (@acdlite)
  *`useOptimistic(state, reducer, rollbackFn)` — automatically revert on mutation failure*

## 🔧 Fixed & Polished

- **React DevTools no longer crashes on components with 1000+ hooks.** ([#30138](https://github.com/facebook/react/pull/30138)) (@hoxyq)
  *Profiling large forms is finally usable again.*

- **Hydration mismatch warnings now include the actual server/client HTML.** ([#30129](https://github.com/facebook/react/pull/30129)) (@rickhanlonii)
  *No more guessing what went wrong — we show you the difference.*

## 🗺️ What's Next

- **[🔥 Coming Soon]** React Compiler in stable — automatic memoization for all ([#28988](https://github.com/facebook/react/issues/28988)) — 👍 1200+
  *The biggest React performance win since hooks. Beta feedback has been phenomenal.*

---

🚀 **[Star us on GitHub](https://github.com/facebook/react)** · 💬 **[Join the discussion](https://github.com/facebook/react/discussions)**
```

### Example 3: Performance & DX Release

```
# 🎉 vite v6.3.0

> **56** commits · **18** issues resolved · **12** contributors
> Apr 1 – Apr 25, 2026 · 67 files · +2450 −780
> 🚀 **[Upgrade now](https://github.com/vitejs/vite/releases/tag/v6.3.0)**

## 🏆 Community Highlights

### ⚡ 2x faster HMR for large projects
[#18900](https://github.com/vitejs/vite/issues/18900) · 👍 167 · 💬 45 · contributed by @patak

> Large monorepos just got a massive boost. @patak rewrote the module graph diffing algorithm — Hot Module Replacement now runs in O(n) instead of O(n²). For a 1000-module project, that's 2x faster updates.

## ✨ Big Things

- **You can now use `await import()` in `vite.config.ts`** — native ESM config loading. ([#19012](https://github.com/vitejs/vite/pull/19012)) (@hi-ogawa)
  *No more dynamic import workarounds in config files*

- **New `define.__DEV__` replacement** works in library mode out of the box. ([#19045](https://github.com/vitejs/vite/pull/19045)) (@sapphi-red)
  *Ship development-only code without ugly `if (process.env.NODE_ENV)` hacks*

## ⚡ Under the Hood

- **CSS processing is 35% faster** by skipping `@import` resolution for node_modules. ([#19033](https://github.com/vitejs/vite/pull/19033)) (@bluwy)
  *Bigger projects feel this most — we measured 35% at 500+ CSS imports*

- **Pre-bundled dependency cache improved** — rebuilds are 50% faster after dependency changes. ([#19056](https://github.com/vitejs/vite/pull/19056)) (@patak)
  *Changed one dep? Don't wait for full re-bundle*

## 🗺️ What's Next

- **[🔥 Coming Soon]** Rolldown-based production build ([#15000](https://github.com/vitejs/vite/issues/15000)) — 👍 340
  *Up to 5x faster builds with the Rust-powered bundler. Beta in v6.4.*

---

🚀 **[Star us on GitHub](https://github.com/vitejs/vite)** · 💬 **[Join the discussion](https://github.com/vitejs/vite/discussions)**
```
