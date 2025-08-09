# AI-driven Autonom Kodgranskare & Refaktor-bot för Git-repo

## Projektöversikt

Det här projektet är en intelligent agent som automatiserar kodgranskning, refaktorering och testgenerering för GitHub Pull Requests (PRs). 

Botens huvudfunktioner:
- Klonar PR-branchen och analyserar kodstil, komplexitet och säkerhetsvarningar.
- Lämnar inline-kommentarer i PR:n via GitHub API med konkreta förändringsförslag (Unified diff).
- Vid utvecklarens godkännande (`/refactor sign-off`) kör boten `git commit --fixup` och pushar automatiskt ändringarna.
- Kör GPT-driven testskrivare när testtäckningen sjunker under 75%.
- Använder OpenAI:s Responses API för att orkestrera flera specialiserade agenter (analys, diff, commit).
- Embeddings-cache för effektiv kontextbaserad analys över repo-historiken.
- RLHF-feedbackloop där maintainers ger tumme upp/ned för att förbättra botens förslag över tid.

---

## Ny Arkitektur: Dashboard & Interaktiv Bot

För att göra verktyget mer användarvänligt och engagerande har vi byggt en **visuell dashboard** och en **interaktiv Slack/Teams-bot** som kopplas ihop med backend.

### Arkitekturöversikt

+----------------+         +----------------+         +------------------+
|                |  API    |                |  API    |                  |
|   Frontend     +-------->+    Backend     +-------->+    GitHub API    |
| (Dashboard UI) |         | (Flask/FastAPI)|         |  (PR, Comments)  |
+-------+--------+         +--------+-------+         +------------------+
        ^                           |
        | WebSocket / Polling       | Bot commands / Events
        |                           v
+-------+--------+          +-------+---------+
|                |          |                 |
| Slack/Teams Bot+<-------->+ Bot Logic Layer |
|                |   API    |                 |
+----------------+          +-----------------+


### Flöde och Funktioner

1. **Backend API**
   - Hanterar data från GitHub (PRs, kommentarer, testcoverage).
   - Sparar och bearbetar feedback och botens events.
   - Tar emot kommandon från Slack/Teams och styr botens agenter.

2. **Dashboard**
   - Visar status och statistik över PR:er, kodkvalitet och botens arbete.
   - Realtidsuppdateringar via WebSocket eller polling.
   - Visualiserar RLHF-feedback och botens utveckling över tid.

3. **Slack/Teams-bot**
   - Interaktiv kommunikation med utvecklare.
   - Tar emot kommandon som `/prstatus`, `/refactor sign-off` och `/feedback`.
   - Skickar notifieringar om ny analys, refaktorering och testgenerering.

4. **Bot Logic Layer**
   - Orkestrerar agenter för statisk analys, diff-generering och commit-logik.
   - Ansvarar för RLHF-feedbackloop och embeddings-cache.

---

## Teknikstack

| Komponent       | Teknologi/Verktyg                     |
|-----------------|-------------------------------------|
| Kodgranskning   | Python, OpenAI Responses API         |
| Backend API     | Flask eller FastAPI                   |
| Databas         | PostgreSQL eller SQLite               |
| Frontend        | React / Vue / Chart.js för grafer    |
| Bot-integration | Slack API (Bolt SDK) / Microsoft Bot Framework |
| CI/CD           | GitHub Actions eller liknande         |

---


