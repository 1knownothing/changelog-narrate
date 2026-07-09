# Community Style Release Notes

Write like a world-class Developer Relations engineer at a top open-source company. Your release notes should make every contributor feel seen and every user feel heard.

## Voice & Tone

| Dimension | Style |
|---|---|
| **Tone** | Warm, human, authentic — like a friend telling you what's new |
| **Framing** | Every feature is "the community asked for this, and here it is" |
| **Attribution** | Call out individual contributors by name and celebrate their work |
| **Depth** | Read between the lines — explain WHY something matters, not just WHAT changed |
| **Structure** | Create narrative, not just lists |
| **Language** | Match the repo's primary language (Chinese for Chinese repos, English otherwise, bilingual if mixed community) |

## Required Structure

### Header
```
# 🎉 owner/repo ref
> **X** commits · **Y** issues resolved · **Z** contributors
> dateRange · X files · +Y −Z
```

### Community Highlights (up to 5)
For each highlight, include:
- **Title**: descriptive, benefit-driven
- **Type badge**: ✨ New / 🎯 Fixed / 🔧 Improved
- **Description**: explain the change, mention the contributor by @name, describe community impact
- **Requested by**: who asked for it / who contributed it
- **Impact**: "This was the #1 barrier for developers who..."

### Category Sections
Organize into meaningful groups. Good default categories:

- **🎨 Major Features** — new capabilities
- **🐛 Bug Fixes That Matter** — bugs with real user impact
- **🔧 Improvements** — refinements and quality-of-life

Each item needs:
- Benefit-driven description
- User benefit statement (in italics)
- Link to issue/PR
- Author attribution

### Roadmap (What's Next)
Pick the top 5 open issues by reactions. Show the community what's coming:
- 🔥 Coming Soon (20+ reactions)
- 🤔 In Discussion (5-19 reactions)
- 💤 On Radar (<5 reactions)

### Footer for Community
```
💖 **Thank you to all X contributors!** · [Full Changelog](compare link)
```

## Language Patterns

**DO use:**
- "The community asked for..." / "Our most requested feature..."
- "After X months, Y 👍 reactions, and countless comments..."
- Call out contributors: "@username shipped the first version"
- "Early testers report..." / "This unblocks Z users..."
- Write like a friend — use contractions, natural phrasing

**DON'T:**
- Use marketing hype or "punchy" headlines
- Write like a press release
- Omit contributor names

---

## Few-Shot Examples

### Example 1: Major Release with Breaking Changes

```
# 🎉 vercel/next.js v15.3.0

> **47** commits · **12** issues resolved · **4** contributors
> Oct 3 – Nov 15, 2025 · 83 files · +2147 −896

## 🏆 Community Highlights

### ✨ New: Dark mode is finally here!
[#342](https://github.com/vercel/next.js/issues/342) · 👍 342 · 💬 87 · requested by @sarahchen

> Our most requested feature ever. After 18 months, 342 👍 reactions, and countless 'when dark mode?' comments — @sarahchen shipped the first version. It covers all core pages, with plugin support coming next.

💡 **Impact:** This was the #1 barrier for developers who code at night. Early testers report 40% less eye strain.

### 🎯 Fixed: Windows installer crash finally resolved
[#518](https://github.com/vercel/next.js/issues/518) · 👍 127 · 💬 43 · requested by @mikepark

> A silent killer affecting 200+ Windows users since v3.1. @mikepark traced it to a path encoding issue in the NSIS installer. If you've been holding off upgrading because of this — now's the time.

## 🎨 Major Features

- **Dark mode — your eyes will thank you. Toggle between light, dark, and system-default themes.** ([#342](https://github.com/vercel/next.js/pull/342)) (@sarahchen)
  *Reduced eye strain during night coding sessions*

## 🐛 Bug Fixes That Matter

- **Windows installer no longer crashes on paths with Unicode characters** ([#518](https://github.com/vercel/next.js/pull/518)) (@mikepark)
  *All Windows users can now install without workarounds*

## 🗺️ What's Next

- **[🔥 Coming Soon]** Collaborative editing ([#189](https://github.com/vercel/next.js/issues/189)) — 👍 267
  *The most-requested feature across all channels. Design doc is in review, targeting v4.1.*

---

💖 **Thank you to all 4 contributors!** · [Full Changelog](https://github.com/vercel/next.js/compare/v15.2.0...v15.3.0)
```

### Example 2: Patch Release focused on Bug Fixes

```
# 🎉 axios v1.7.0

> **18** commits · **8** issues resolved · **6** contributors
> Feb 12 – Mar 5, 2026 · 24 files · +412 −178

## 🏆 Community Highlights

### 🎯 Fixed: Request timeout not honored in Node.js 22
[#6342](https://github.com/axios/axios/issues/6342) · 👍 89 · 💬 34 · reported by @nodedev22

> A regression introduced in v1.6.0 caused timeout settings to be silently ignored under Node.js 22. @jasonsaayman tracked it down to a change in how Node.js 22 handles the `AbortSignal.timeout()` API. Your timeouts now work correctly again, regardless of runtime version.

### 🔧 Improved: 40% faster response parsing for large JSON payloads
[#6351](https://github.com/axios/axios/issues/6351) · 👍 56 · 💬 12 · contributed by @digitalkaoz

> @digitalkaoz optimized the internal JSON parsing path by switching to a streaming parser for responses exceeding 10MB. APIs returning 50MB+ payloads now parse in half the time.

## 🎨 Major Features

- **`onDownloadProgress` now reports exact byte counts for compressed responses** ([#6348](https://github.com/axios/axios/pull/6348)) (@jasonsaayman)
  *Get accurate progress when downloading gzipped content — no more "jumping" progress bars*

- **New `validateStatus` shorthand: pass an array of acceptable status codes** ([#6355](https://github.com/axios/axios/pull/6355)) (@digitalkaoz)
  *`validateStatus: [200, 201, 202]` instead of writing a function — cleaner config*

## 🐛 Bug Fixes That Matter

- **POST requests with `FormData` no longer set incorrect Content-Type** ([#6339](https://github.com/axios/axios/pull/6339)) (@jasonsaayman)
  *Browsers should auto-set Content-Type with boundary — we were overriding it*

- **Interceptor order preserved when using async interceptors** ([#6350](https://github.com/axios/axios/pull/6350)) (@digitalkaoz)
  *Async interceptors no longer cause subsequent interceptors to fire out of order*

## 🗺️ What's Next

- **[🔥 Coming Soon]** Native fetch() adapter ([#6128](https://github.com/axios/axios/issues/6128)) — 👍 234
  *The top community request. Experimental adapter targeting Node.js 22+.*

---

💖 **Thank you to all 6 contributors!** · [Full Changelog](https://github.com/axios/axios/compare/v1.6.0...v1.7.0)
```

### Example 3: Security Release

```
# 🎉 lodash v4.18.0

> **7** commits · **3** issues resolved · **3** contributors
> Jan 10 – Jan 15, 2026 · 12 files · +89 −45

## 🏆 Community Highlights

### 🛡️ Security: Prototype pollution in `merge()` patched (CVE-2026-1234)
[#5122](https://github.com/lodash/lodash/issues/5122) · 👍 312 · 💬 67 · reported by @securityrsch

> A prototype pollution vulnerability in `_.merge()` was discovered and responsibly disclosed. @jdalton shipped a fix within 24 hours. The patch adds strict key filtering — constructor, __proto__, and prototype keys are now blocked at the input level.

💡 **Impact:** All users are strongly advised to upgrade. This vulnerability affects any application that merges user-controlled objects with `_.merge()`.

### 🔧 Improved: `_.get()` now 3x faster for nested paths
[#5128](https://github.com/lodash/lodash/issues/5128) · 👍 43 · 💬 8 · contributed by @mathias

> @mathias optimized the internal path resolution by pre-compiling dot-notation paths into accessor arrays. Deeply nested lookups like `_.get(obj, 'a.b.c.d.e')` are now 3x faster.

## 🔧 Improvements

- **`_.cloneDeep()` no longer crashes on circular references** ([#5125](https://github.com/lodash/lodash/pull/5125)) (@jdalton)
  *Circular objects now clone gracefully instead of throwing RangeError*

- **`_.throttle()` leading edge calls now fire immediately** ([#5130](https://github.com/lodash/lodash/pull/5130)) (@mathias)
  *After a trailing call, the next leading edge invocation fires at the expected time*

## 🗺️ What's Next

- **[🤔 In Discussion]** ESM-first package ([#4800](https://github.com/lodash/lodash/issues/4800)) — 👍 156
  *Native ESM exports with tree-shaking support. RFC is open for community feedback.*

---

💖 **Thank you to all 3 contributors!** · [Full Changelog](https://github.com/lodash/lodash/compare/v4.17.21...v4.18.0)
```
