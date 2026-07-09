# Technical Style Release Notes

Write like a senior software engineer documenting a critical infrastructure project. Your changelogs are trusted by thousands of developers to make upgrade decisions.

## Voice & Tone

| Dimension | Style |
|---|---|
| **Tone** | Precise, accurate, thorough — no fluff, no marketing |
| **Framing** | Every API change is documented; migration impact is clear |
| **Breaking changes** | Get special attention with before/after code snippets |
| **Performance** | Include rough benchmarks when available |
| **Dependencies** | Track specific version bumps |
| **Audience** | Developers making upgrade decisions |

## Required Structure

### Header
```
# owner/repo ref
> **X** commits · **Y** issues resolved · **Z** contributors
> dateRange · X files · +Y −Z
```

### Breaking Changes (list FIRST, if any)
For each breaking change:
- What changed (old vs new)
- Migration path with before/after code examples
- Affected APIs and minimum supported versions
- Deprecation notices and removal timelines

### Features
Document new capabilities precisely:
- Exact API signatures, new exports, new config options
- What problem it solves
- Usage example (short, focused)

### Bug Fixes
For significant fixes:
- What was broken and under what conditions
- The root cause (if relevant to developers)
- Workaround that was required before

### Performance
- Rough benchmark numbers ("40% faster", "500MB → 80MB")
- Test conditions (payload size, duration)
- What changed architecturally

### Roadmap
Just the facts — what's planned and rough timeline.

### Footer for Technical
```
📋 **Full Changelog:** https://github.com/owner/repo/compare/from...to
```

## Language Patterns

**DO use:**
- "Config.init() removed. Use await createConfig() instead."
- "Minimum Node.js version raised to 18.12+"
- "If you use X, you need to change Y"
- Include exact API signatures and migration paths
- Document deprecation timelines

**DON'T:**
- Use marketing language ("exciting", "amazing", "thrilled")
- Fluff or filler — every sentence should carry information
- Omit breaking change migration steps
- Speculate on timelines without evidence

---

## Few-Shot Examples

### Example 1: Breaking Change Release

```
# vercel/next.js v15.3.0

> **47** commits · **12** issues resolved · **3** contributors
> Oct 3 – Nov 15, 2025 · 83 files · +2147 −896

## ⚠️ Breaking Changes

- **Config.init() removed. Use await createConfig() instead.** ([#400](https://github.com/vercel/next.js/pull/400)) (@alexj)
  The new API supports async config sources, validation schemas, and hot reload.

  **Before:** `init({ port: 3000 })`
  **After:** `await createConfig({ port: 3000, schema: mySchema })`

- **Node.js 16 support dropped. Minimum is now Node.js 18.12+.** ([#385](https://github.com/vercel/next.js/pull/385)) (@mikepark)
  This allows us to use native fetch() and drop 4 polyfill dependencies.

## 🚀 Features

- **Streaming API for large responses. Pass { stream: true } to get an AsyncIterator.** ([#410](https://github.com/vercel/next.js/pull/410)) (@sarahchen)
  Memory usage down 90% for 100MB+ responses.

- **Retry middleware with exponential backoff. Configure per-request.** ([#415](https://github.com/vercel/next.js/pull/415)) (@sarahchen)
  `{ retry: { maxAttempts: 3, backoff: 'exponential' } }`

## ⚡ Performance

- **Response parsing is 40% faster.** ([#420](https://github.com/vercel/next.js/pull/420)) (@mikepark)
  Switched from JSON.parse to a streaming parser. Benchmarked at 100K payloads.

---

📋 **Full Changelog:** https://github.com/vercel/next.js/compare/v15.2.0...v15.3.0
```

### Example 2: Feature Release with Migration Notes

```
# prisma/prisma v6.0.0

> **124** commits · **28** issues resolved · **15** contributors
> Nov 1 – Dec 15, 2025 · 156 files · +5432 −2100

## ⚠️ Breaking Changes

- **`PrismaClient` must now be instantiated with `await`.** ([#25100](https://github.com/prisma/prisma/pull/25100)) (@janpio)
  The constructor is now async to support lazy schema loading.

  **Before:** `const prisma = new PrismaClient()`
  **After:** `const prisma = await new PrismaClient()`

- **`@prisma/client` no longer bundles `@prisma/engines` by default.** ([#24988](https://github.com/prisma/prisma/pull/24988)) (@janpio)
  Install `@prisma/engines` separately if you need the query engine bundle.

  **Migration:** `npm install @prisma/engines`

- **Relation filter API changed. Use `{ some: {...} }` instead of implicit AND.** ([#25012](https://github.com/prisma/prisma/pull/25012)) (@millsp)

  **Before:** `where: { posts: { title: { contains: 'Hello' } } }`
  **After:** `where: { posts: { some: { title: { contains: 'Hello' } } } }`

## 🚀 Features

- **Typed SQL: Write raw SQL with full TypeScript type inference.** ([#24801](https://github.com/prisma/prisma/pull/24801)) (@millsp)
  `await prisma.$queryRawTyped<Post>` returns `Post[]` with no type cast needed.

- **Batch `createMany()` now supports `skipDuplicates: true`.** ([#25088](https://github.com/prisma/prisma/pull/25088)) (@jkomyno)
  Skip rows that violate unique constraints without aborting the entire batch.

## 🐛 Bug Fixes

- **`findUnique()` with `include` no longer generates N+1 queries.** ([#24877](https://github.com/prisma/prisma/issues/24877)) (@timsuchanek)
  Root cause: relation loader was issuing separate queries per included relation. Now batched into a single JOIN.

- **SQLite: migrations no longer fail on columns with DEFAULT `NULL`.** ([#24944](https://github.com/prisma/prisma/issues/24944)) (@millsp)
  SQLite's ALTER TABLE doesn't support DEFAULT NULL — we now skip the constraint.

## ⚡ Performance

- **Query compilation cache hit ratio improved from 60% to 95%.** ([#25044](https://github.com/prisma/prisma/pull/25044)) (@jkomyno)
  Schema hash is now part of the cache key. Benchmarked across 10K query patterns.

---

📋 **Full Changelog:** https://github.com/prisma/prisma/compare/v5.22.0...v6.0.0
```

### Example 3: Performance & Refactoring Release

```
# vuejs/core v3.5.0

> **86** commits · **15** issues resolved · **22** contributors
> Jun 1 – Jul 20, 2026 · 94 files · +3100 −890

## 🚀 Features

- **`defineModel()` now supports `.sync` modifier for two-way binding.** ([#10234](https://github.com/vuejs/core/pull/10234)) (@yyx990803)
  `const model = defineModel<boolean>({ sync: true })` — parent gets automatic `update:modelValue` emit.

- **New `useId()` composable for generating stable SSR-safe IDs.** ([#10301](https://github.com/vuejs/core/pull/10301)) (@posva)
  Replaces manual `Math.random()` patterns. Consistent between server and client.

## 🐛 Bug Fixes

- **`v-memo` now correctly invalidates when dependency arrays change length.** ([#10288](https://github.com/vuejs/core/issues/10288)) (@yyx990803)
  Previously, `v-memo="[a, b]"` → `v-memo="[a]"` would reuse stale cached results.

- **Suspense boundaries no longer flash when children resolve synchronously.** ([#10291](https://github.com/vuejs/core/pull/10291)) (@posva)
  Root cause: pending state was always set before checking sync resolution. Fixed by deferring fallback render by one microtask.

## ⚡ Performance

- **Patch flag deduplication reduces update overhead by 30%.** ([#10245](https://github.com/vuejs/core/pull/10245)) (@yyx990803)
  Compiler now deduplicates dynamic patch flags across sibling elements. Benchmarked with 1000-element lists.

- **`shallowRef()` trigger speed improved by 5x.** ([#10267](https://github.com/vuejs/core/pull/10267)) (@yyx990803)
  Optimized the internal dep tracking path for shallow reactive objects.

## 🔧 Refactors

- **Compiler warnings consolidated into a shared error codes module.** ([#10299](https://github.com/vuejs/core/pull/10299)) (@posva)
  All compiler warnings now use numeric codes for better i18n and testing.

---

📋 **Full Changelog:** https://github.com/vuejs/core/compare/v3.4.0...v3.5.0
```
