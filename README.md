# ⚔️ Vicilingo

> **Conquest of Language.** A self-hosted, modular language learning web app built to automate personalized study workflows using spatial mechanics and free-tier LLM integrations.

Vicilingo replaces scattered notebooks, vocabulary apps, and disjointed text files by organizing multiple languages onto a single, draggable HTML5 Canvas mind map. It transforms your (my) personal study strategy (assessing topics, generating targeted exercises, interactive roleplay, and tracking dynamic pools) into a unified, streamlined homelab.

See it in action!
https://antixbasipek.taile1bff7.ts.net/language

Check out my To-Do list!
https://antixbasipek.taile1bff7.ts.net/synodos?path=%2FLobby&node_id=45

[Heavily WIP and early in development. AI Assisted.]
---

## 🗺️ Core Architecture & Features

*   **Spatial Conquest Map (HTML5 Canvas):** A performance-focused, zero-dependency draggable and zoomable canvas map displaying your language tracks as node clusters (e.g., Japanese A1 extending to the West, German to the South).
*   **Automated Progress Hub:** Keeps your active learning footprint compact. Topics are categorized dynamically by performance: *Bad Performance, Meh Performance, Good Performance, and Memorized*. Correct answers grant XP; time decay and mistakes drop XP, shifting nodes across performance pools.
*   **The Ingredient Gym (Cooking Minigame):** A dynamic staging area where you select topics as "ingredients" and dial in custom parameters (difficulty, character RP style, question types, alphabet configurations). The interface compiles them into a custom prompt payload.
*   **On-Demand LLM Orchestration:** Integrates with free-tier APIs via OpenRouter to generate clean, JSON-parsed exercises, evaluate free-form text, handle grammar Q&As, and spin up context-aware RP sessions.
*   **Modular Node Filesystem:** Avoids heavy, monolithic database reads. Language paths are loaded dynamically from separate, lightweight static files (e.g., `jp_dummy.json`, `de_section1.json`).

---
