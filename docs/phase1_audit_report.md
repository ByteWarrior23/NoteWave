# NoteWave — Phase 1 Audit Report

> **PROJECT:** NoteWave — A RAG-powered document intelligence platform (FastAPI backend + Next.js 16 frontend) that lets users upload PDFs, chat with them via Gemini/Ollama, and generate multi-modal study content (podcasts, flashcards, quizzes, knowledge graphs, debates, summaries).

---

## 1. Complete File Inventory

### Root (`/`)

| File | Purpose |
|------|---------|
| [`.gitignore`](file:///e:/NoteWave-main/NoteWave-main/.gitignore) | Root-level git ignore rules |
| [`LICENSE`](file:///e:/NoteWave-main/NoteWave-main/LICENSE) | MIT license file |
| [`PROJECT_DOCUMENTATION.md`](file:///e:/NoteWave-main/NoteWave-main/PROJECT_DOCUMENTATION.md) | Comprehensive project docs (architecture, API reference, component docs) |
| [`README.md`](file:///e:/NoteWave-main/NoteWave-main/README.md) | User-facing readme with setup instructions and screenshots |
| [`docker-compose.yml`](file:///e:/NoteWave-main/NoteWave-main/docker-compose.yml) | Docker Compose config for backend + frontend services |
| [`render.yaml`](file:///e:/NoteWave-main/NoteWave-main/render.yaml) | Render.com deployment blueprint for the backend |

### `docs/`

| File | Purpose |
|------|---------|
| [`docs/NoteWave_Project_Documentation.docx`](file:///e:/NoteWave-main/NoteWave-main/docs/NoteWave_Project_Documentation.docx) | Word version of project documentation |
| [`docs/notewave-dashboard.png`](file:///e:/NoteWave-main/NoteWave-main/docs/notewave-dashboard.png) | Dashboard screenshot used in README.md |

### `backend/`

| File | Purpose |
|------|---------|
| [`backend/.env.example`](file:///e:/NoteWave-main/NoteWave-main/backend/.env.example) | Example environment variables template |
| [`backend/Dockerfile`](file:///e:/NoteWave-main/NoteWave-main/backend/Dockerfile) | Docker build for FastAPI backend |
| [`backend/main.py`](file:///e:/NoteWave-main/NoteWave-main/backend/main.py) | FastAPI app: routes, request models, job queue, error handling |
| [`backend/rag.py`](file:///e:/NoteWave-main/NoteWave-main/backend/rag.py) | Core RAG engine: embeddings, vector DB, LLM calls, all studio generators |
| [`backend/key_pool.py`](file:///e:/NoteWave-main/NoteWave-main/backend/key_pool.py) | Round-robin API key pool with rate-limit detection |
| [`backend/tts.py`](file:///e:/NoteWave-main/NoteWave-main/backend/tts.py) | ElevenLabs TTS integration for podcast audio |
| [`backend/requirements.txt`](file:///e:/NoteWave-main/NoteWave-main/backend/requirements.txt) | Python dependency list |

### `frontend/` (config files)

| File | Purpose |
|------|---------|
| [`frontend/.gitignore`](file:///e:/NoteWave-main/NoteWave-main/frontend/.gitignore) | Frontend-specific git ignore rules |
| [`frontend/Dockerfile`](file:///e:/NoteWave-main/NoteWave-main/frontend/Dockerfile) | Docker build for Next.js frontend |
| [`frontend/components.json`](file:///e:/NoteWave-main/NoteWave-main/frontend/components.json) | shadcn/ui configuration |
| [`frontend/eslint.config.mjs`](file:///e:/NoteWave-main/NoteWave-main/frontend/eslint.config.mjs) | ESLint configuration |
| [`frontend/next.config.ts`](file:///e:/NoteWave-main/NoteWave-main/frontend/next.config.ts) | Next.js config with `/api` proxy rewrite rules |
| [`frontend/package.json`](file:///e:/NoteWave-main/NoteWave-main/frontend/package.json) | npm dependencies and scripts |
| [`frontend/package-lock.json`](file:///e:/NoteWave-main/NoteWave-main/frontend/package-lock.json) | Lockfile for reproducible installs |
| [`frontend/postcss.config.js`](file:///e:/NoteWave-main/NoteWave-main/frontend/postcss.config.js) | PostCSS config for Tailwind |
| [`frontend/tailwind.config.js`](file:///e:/NoteWave-main/NoteWave-main/frontend/tailwind.config.js) | Tailwind CSS config with shadcn tokens |
| [`frontend/tsconfig.json`](file:///e:/NoteWave-main/NoteWave-main/frontend/tsconfig.json) | TypeScript compiler config |

### `frontend/src/app/`

| File | Purpose |
|------|---------|
| [`src/app/layout.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/app/layout.tsx) | Root layout: Inter font, metadata, ThemeProvider wrapper |
| [`src/app/page.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/app/page.tsx) | Main page: entire dashboard (chat, sidebars, studios, upload, state management) — 843 lines |
| [`src/app/providers.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/app/providers.tsx) | Client-side ThemeProvider (next-themes) |
| [`src/app/globals.css`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/app/globals.css) | Global CSS: shadcn tokens, markdown styling, utility classes |
| [`src/app/favicon.ico`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/app/favicon.ico) | Browser tab icon |
| [`src/app/api/[...path]/route.ts`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/app/api/%5B...path%5D/route.ts) | Catch-all API proxy: forwards all `/api/*` to FastAPI backend |

### `frontend/src/lib/`

| File | Purpose |
|------|---------|
| [`src/lib/api.ts`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/lib/api.ts) | API_BASE URL constant + error message extractor |
| [`src/lib/commands.ts`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/lib/commands.ts) | Command palette definitions for `/podcast`, `/flashcards`, etc. |
| [`src/lib/utils.ts`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/lib/utils.ts) | `cn()` utility (clsx + twMerge) — standard shadcn helper |
| [`src/lib/agents.ts`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/lib/agents.ts) | Research agent metadata (Skeptic/Weaver/Veritas) for debate UI |

### `frontend/src/types/`

| File | Purpose |
|------|---------|
| [`src/types/force-graph.d.ts`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/types/force-graph.d.ts) | TypeScript declarations for `react-force-graph-3d` library |

### `frontend/src/components/`

| File | Purpose |
|------|---------|
| [`components/knowledge-graph.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/knowledge-graph.tsx) | 3D force graph renderer using `react-force-graph-3d` |
| [`components/landing/LandingPage.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/landing/LandingPage.tsx) | Landing/hero page with drag-and-drop upload |
| [`components/dashboard/CommandPalette.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/dashboard/CommandPalette.tsx) | `/command` autocomplete overlay |
| [`components/dashboard/SidebarLeft.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/dashboard/SidebarLeft.tsx) | Left sidebar: document library, upload dialog, theme toggle |
| [`components/dashboard/SidebarRight.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/dashboard/SidebarRight.tsx) | Right sidebar: studio selector + renders active studio |

### `frontend/src/components/dashboard/studios/`

| File | Purpose |
|------|---------|
| [`studios/PodcastStudio.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/dashboard/studios/PodcastStudio.tsx) | AI podcast script viewer with TTS playback |
| [`studios/FlashcardsStudio.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/dashboard/studios/FlashcardsStudio.tsx) | 3D flip flashcard deck |
| [`studios/GraphStudio.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/dashboard/studios/GraphStudio.tsx) | Knowledge graph visualization (3D + 2D fallback) |
| [`studios/DebateStudio.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/dashboard/studios/DebateStudio.tsx) | Multi-agent debate transcript viewer |
| [`studios/VaultStudio.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/dashboard/studios/VaultStudio.tsx) | Document integrity/truth audit dashboard |
| [`studios/QuizStudio.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/dashboard/studios/QuizStudio.tsx) | Interactive multiple-choice quiz |
| [`studios/SummaryStudio.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/dashboard/studios/SummaryStudio.tsx) | Document summary with markdown rendering |
| [`studios/VoiceStudio.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/dashboard/studios/VoiceStudio.tsx) | Browser speech recognition for voice input |
| [`studios/SettingsStudio.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/dashboard/studios/SettingsStudio.tsx) | App settings: API key, focus mode, auto-audit toggles |

### `frontend/src/components/ui/` (shadcn/ui primitives)

| File | Used by |
|------|---------|
| [`ui/avatar.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/avatar.tsx) | ✅ `page.tsx` |
| [`ui/badge.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/badge.tsx) | ✅ VaultStudio, SettingsStudio, QuizStudio, PodcastStudio, FlashcardsStudio |
| [`ui/button.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/button.tsx) | ✅ Multiple components |
| [`ui/card.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/card.tsx) | ✅ knowledge-graph.tsx, studios |
| [`ui/dialog.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/dialog.tsx) | ✅ LandingPage, SidebarLeft |
| [`ui/input.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/input.tsx) | ✅ page.tsx, LandingPage, SidebarLeft |
| [`ui/progress.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/progress.tsx) | ✅ VaultStudio, SettingsStudio, QuizStudio, FlashcardsStudio |
| [`ui/scroll-area.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/scroll-area.tsx) | ✅ page.tsx, SidebarLeft |
| [`ui/select.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/select.tsx) | ❌ **Zero imports anywhere** |
| [`ui/separator.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/separator.tsx) | ❌ **Zero imports anywhere** |
| [`ui/switch.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/switch.tsx) | ✅ SettingsStudio |
| [`ui/tabs.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/tabs.tsx) | ❌ **Zero imports anywhere** |
| [`ui/textarea.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/textarea.tsx) | ✅ FlashcardsStudio |
| [`ui/toast.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/toast.tsx) | ✅ page.tsx |

---

## 2. Removal Candidates

### 🟢 HIGH confidence — Safe to remove

| Item | Reason |
|------|--------|
| No `__pycache__/`, `.pyc`, `node_modules/`, `.DS_Store`, `.vscode/`, `.idea/` found | ✅ Already clean — `.gitignore` covers these, none committed |
| No `*.old`, `*.bak`, duplicate files found | ✅ Clean |
| No `console.log` debug statements found | ✅ Clean |
| `console.error` statements (8 occurrences) | ⚠️ These are legitimate error-logging, not debug — **KEEP** |
| [`ui/select.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/select.tsx) | shadcn/ui component installed but **zero imports** anywhere in the codebase |
| [`ui/separator.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/separator.tsx) | shadcn/ui component installed but **zero imports** anywhere in the codebase |
| [`ui/tabs.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/ui/tabs.tsx) | shadcn/ui component installed but **zero imports** anywhere in the codebase |

### 🟡 MEDIUM confidence — Asking before removing

| Item | Reason | Reference check |
|------|--------|-----------------|
| [`docs/NoteWave_Project_Documentation.docx`](file:///e:/NoteWave-main/NoteWave-main/docs/NoteWave_Project_Documentation.docx) | Appears to be a Word export of `PROJECT_DOCUMENTATION.md`. Not referenced by any code or script. Likely a submission artifact. | Searched entire repo for `NoteWave_Project_Documentation` — **zero references** in code/config. Only exists as a file in `/docs/`. |
| [`components/knowledge-graph.tsx`](file:///e:/NoteWave-main/NoteWave-main/frontend/src/components/knowledge-graph.tsx) | Standalone 3D graph component. **Not imported by any file.** The `GraphStudio.tsx` component has its own inline ForceGraph3D rendering + 2D fallback — this file appears to be an earlier standalone version that was superseded. | Searched for `knowledge-graph` and `KnowledgeGraph` — **zero import references** in any `.ts`/`.tsx` file. Only mentioned in `PROJECT_DOCUMENTATION.md` as a description. |
| Backend `/chat/stream` SSE endpoint ([`main.py` L283-305](file:///e:/NoteWave-main/NoteWave-main/backend/main.py#L283-L305)) | The frontend uses **polling** (`POST /chat` → job queue → `GET /chat/status/{id}`). The SSE endpoint exists in the backend but is **never called** by the frontend. However, it IS functional code and could be used by external clients. | Searched for `chat/stream` in frontend — **zero references**. The `stream_chat_answer` function IS imported in `main.py` and wired to a route, so it's not dead Python code — it's just an unused API endpoint from the frontend's perspective. |
| `langchain-google-genai` in [`requirements.txt`](file:///e:/NoteWave-main/NoteWave-main/backend/requirements.txt#L10) | Listed as a dependency but **never imported** anywhere in Python code. The backend uses `google-genai` (the official SDK) directly, not the LangChain wrapper. | Searched for `langchain_google_genai` across all `.py` files — **zero imports**. |
| `@radix-ui/react-select` in [`package.json` L16](file:///e:/NoteWave-main/NoteWave-main/frontend/package.json#L16) | npm dependency for the Select component — but `ui/select.tsx` is never imported (see HIGH confidence above). The Radix dependency can be removed with the component. | Confirmed: zero usage of Select anywhere. |
| `@radix-ui/react-separator` in [`package.json` L17](file:///e:/NoteWave-main/NoteWave-main/frontend/package.json#L17) | `"@radix-ui/react-separator": "^1.1.8"` — a **direct dependency**, listed explicitly. Becomes unused once `separator.tsx` is removed. | Confirmed: direct `dependencies` entry at L17; zero imports of the component. |
| `@radix-ui/react-tabs` in [`package.json` L20](file:///e:/NoteWave-main/NoteWave-main/frontend/package.json#L20) | `"@radix-ui/react-tabs": "^1.1.13"` — a **direct dependency**, listed explicitly. Becomes unused once `tabs.tsx` is removed. | Confirmed: direct `dependencies` entry at L20; zero imports of the component. |

### 🔴 DO NOT TOUCH — Protected files

| File | Status |
|------|--------|
| `chroma_db/` | Not committed (in `.gitignore`) ✅ |
| `documents/` | Not committed (in `.gitignore`) ✅ |
| `.env` / `.env.example` | Protected ✅ |
| `requirements.txt` | Protected (flagged unused dep above, won't remove without approval) ✅ |
| `package.json` | Protected (flagged unused dep above, won't remove without approval) ✅ |
| `docker-compose.yml` | Protected ✅ |
| `render.yaml` | Protected ✅ |
| `PROJECT_DOCUMENTATION.md` | Protected ✅ |
| `LICENSE` | Protected ✅ |
| All studio components | All imported by `SidebarRight.tsx` — confirmed active ✅ |
| `agents.ts` | Imported by `DebateStudio.tsx` — confirmed active ✅ |
| `force-graph.d.ts` | Type declarations for `react-force-graph-3d` — needed for build ✅ |
| `docs/notewave-dashboard.png` | Referenced in `README.md` — confirmed active ✅ |

---

## 3. Additional Observations

### `.gitignore` gaps
The root `.gitignore` covers `__pycache__/` but is missing `*.pyc` (individual files, not just dirs). Worth adding for completeness.

### Redundant API proxy mechanism
The frontend has **two** mechanisms for reaching the backend:
1. `next.config.ts` rewrites (`/api/:path*` → `http://127.0.0.1:8000/api/:path*`) — server-side proxy
2. `src/app/api/[...path]/route.ts` — catch-all API route that manually proxies requests

These are **redundant**. The Next.js rewrite handles it at the framework level; the catch-all route does the same thing in application code. However, both are functional and neither is "dead" — they serve different deployment scenarios (rewrites work in dev, the catch-all works in production where rewrites may not apply).

> [!IMPORTANT]
> **Not flagging for removal** — this is a behavioral observation. Both mechanisms are intentional and one may be needed depending on deployment target. Suggesting this as a Phase 3 note.

### `framer-motion` installed but unused
`framer-motion` is in `package.json` dependencies but is **never imported** in any source file currently. It's listed as a future dependency (and will be heavily used in the landing page redesign).

> [!NOTE]
> **Not flagging for removal** — we'll actively use this for the frontend redesign.

### Backend is well-structured for its size
`main.py` (407 lines) and `rag.py` (911 lines) are on the larger side but still cohesive. `rag.py` could benefit from splitting in the future, but per your instructions, I won't fragment files that haven't genuinely outgrown a single-file layout. The key-pool and TTS modules are already properly separated.

---

## 4. Re-verification Pass — 2026-10-02

Every flagged claim was re-checked against the working tree. No files have been deleted yet; all removal candidates are still present.

### Confirmed unchanged

| Claim | Result |
|-------|--------|
| `ui/select.tsx`, `ui/separator.tsx`, `ui/tabs.tsx` have zero imports | ✅ Confirmed — no `components/ui/select\|separator\|tabs` import in any `.ts`/`.tsx` |
| `components/knowledge-graph.tsx` is orphaned | ✅ Confirmed — only self-reference is its own `export default function KnowledgeGraph` |
| `langchain-google-genai` is unimported | ✅ Confirmed — backend imports only `langchain_chroma`, `langchain_community`, `langchain_core`, `langchain_text_splitters` |
| `/chat/stream` unused by frontend | ✅ Confirmed — zero `chat/stream` references in `frontend/src` |
| No `console.log` statements | ✅ Confirmed — 0 matches in `frontend/src` |

### Corrections applied

| Original claim | Correct value | Method |
|----------------|---------------|--------|
| `@radix-ui/react-separator` "Not listed explicitly, but is a sub-dependency" | **Wrong.** Direct dependency: `"@radix-ui/react-separator": "^1.1.8"` | `frontend/package.json` L17 |
| `@radix-ui/react-tabs` "Not listed explicitly… no separate dep entry" | **Wrong.** Direct dependency: `"@radix-ui/react-tabs": "^1.1.13"` | `frontend/package.json` L20 |
| `console.error` — 6 occurrences | 8 occurrences in `frontend/src` | `Select-String` over `frontend/src/**/*.ts{,x}` |
| `page.tsx` — 844 lines | 843 lines | `Get-Content … .Count` |
| `main.py` — 408 lines | 407 lines | `Get-Content … .Count` (`rag.py` = 911 confirmed) |

> [!NOTE]
> The line-count deltas are trailing-newline artifacts, not a change in the files. The Radix findings were substantive errors: **three** direct dependencies (`react-select`, `react-separator`, `react-tabs`) become removable alongside their components, not one.

### Revised removal counts

| Item | Count |
|------|-------|
| **HIGH confidence removals** | 3 component files + 3 Radix dependency entries (`react-select`, `react-separator`, `react-tabs`) |
| **MEDIUM confidence — need approval** | 3 items (unchanged) |

**Nothing has been removed.** The Phase 1 approval gate is still open.

---

## Summary of Proposed Actions

| Action | Count |
|--------|-------|
| **HIGH confidence removals** | 3 files (`select.tsx`, `separator.tsx`, `tabs.tsx`) |
| **MEDIUM confidence — need your approval** | 3 items (`NoteWave_Project_Documentation.docx`, `knowledge-graph.tsx`, `langchain-google-genai` dep) |
| **Behavioral suggestions (Phase 3 notes)** | 2 (redundant proxy, `/chat/stream` SSE endpoint) |
| **Protected / confirmed active** | Everything else — no changes |

> [!NOTE]
> Updated 2026-10-02 after re-verification — HIGH confidence removals now also cover the 3 direct Radix dependency entries (`react-select`, `react-separator`, `react-tabs`) that accompany the unused components. See §4.

---

**⏸ Stopping here. Awaiting your approval before proceeding to Phase 2.**

Please confirm:
1. ✅ or ❌ on the 3 HIGH confidence removals (`select.tsx`, `separator.tsx`, `tabs.tsx` + their 3 Radix deps)
2. ✅ or ❌ on each of the 3 MEDIUM confidence items
3. Any additional files you want preserved or removed
