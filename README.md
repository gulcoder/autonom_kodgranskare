
# AutoReview-Bot: Autonom Kodgranskare & Refaktor-Agent

**En AI-driven bot som automatiserar kodgranskning, föreslår konkreta refaktoreringar och implementerar dem direkt i dina Pull Requests på GitHub.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Development](https://img.shields.io/badge/status-development-orange.svg)]()

---

## Beskrivning

Detta projekt är en autonom agent utformad för att effektivisera och förbättra kodkvaliteten i Git-baserade arbetsflöden. När en ny Pull Request (PR) skapas, aktiveras boten för att genomföra en grundlig analys av den föreslagna koden. Den fungerar som en outtröttlig, objektiv granskare som hjälper utvecklingsteam att upprätthålla höga standarder för kodstil, prestanda och säkerhet.

Genom att använda en avancerad multi-agent-arkitektur, orkestrerad via det nya **Responses API** (lanserat mars 2025), kan boten delegera specifika uppgifter – från statisk analys till generering av ändrings-patchar – för maximal effektivitet. Resultatet är konkreta, implementerbara förslag som presenteras direkt som kommentarer i PR:en, vilket minimerar den manuella ansträngningen för både författare och granskare.

## Kärnfunktioner

-   **🤖 Automatiserad Granskning vid Pull Requests**: Boten startar automatiskt sitt analysflöde så fort en ny PR öppnas.
-   **📊 Mångfacetterad Kodanalys**: Granskar koden ur flera perspektiv:
    -   **Kodstil**: Säkerställer konsekvent formatering och stil enligt projektets riktlinjer.
    -   **Komplexitet**: Identifierar onödigt komplexa funktioner och klasser (cyklomatisk komplexitet).
    -   **Säkerhet**: Letar efter vanliga sårbarheter och "code smells".
-   **✍️ Konkreta Förbättringsförslag**: Istället för vaga kommentarer publicerar boten **inline-kommentarer** med färdiga kod-patchar i *Unified Diff*-format.
-   **✅ Sömlös Implementering med `sign-off`**: Genom att författaren skriver en enkel kommentar (`/refactor sign-off`), instrueras boten att automatiskt applicera sina egna förslag, skapa en `fixup`-commit och pusha ändringarna till PR-branchen.

## Hur det fungerar

1.  **Pull Request Skapas**: En utvecklare skapar en ny PR i GitHub-repot.
2.  **Webhook Aktiveras**: En webhook notifierar AutoReview-Bot om händelsen.
3.  **Agent-orkestrering**: Huvudprocessen använder **Responses API** för att starta och koordinera tre specialiserade agenter:
    -   **Analys-agenten**: Klonar PR-branchen och utför statisk analys.
    -   **Diff-agenten**: Tar emot output från analys-agenten och genererar konkreta kodförslag i diff-format.
    -   **Commit-agenten**: Övervakar PR:en för `sign-off`-kommandon och hanterar Git-logiken (`commit --fixup`, `push`).
4.  **Förslag Publiceras**: Diff-agenten använder GitHub-API:et för att posta förslagen som inline-kommentarer direkt på de relevanta kodraderna.
5.  **Utvecklaren Godkänner**: Om utvecklaren gillar förslagen, publiceras kommentaren `/refactor sign-off`.
6.  **Boten Genomför Ändringar**: Commit-agenten fångar upp kommandot, applicerar patcharna, skapar en eller flera `fixup`-commits och pushar till branchen, vilket uppdaterar PR:en.

## Avancerade Funktioner & Framtidsplaner

Detta projekt innehåller även flera avancerade utmaningar för att ytterligare förbättra botens prestanda och intelligens.

-   **⚡️ Embeddings-cache för Kontexthantering**: För att ge snabbare och mer relevanta förslag skapas en cache med vector embeddings av hela repo-historiken. Detta låter agenten snabbt förstå den befintliga kodbasens arkitektur och stil.
-   **🧪 GPT-driven Enhetstest-generator**: Om en PR orsakar att kodtäckningen (`code coverage`) sjunker under en tröskel (t.ex. 75 %), kan en specialiserad agent automatiskt skriva och föreslå nya enhetstester för den tillagda koden.
-   **👍👎 RLHF-loop för Kontinuerlig Förbättring**: Genom att låta en maintainer ge "tumme upp" eller "tumme ned" på botens förslag implementeras en Reinforcement Learning from Human Feedback-loop. Denna feedback viktas och används för att finjustera de underliggande modellerna inför framtida körningar, vilket gör boten smartare över tid.

## Teknisk Stack

-   **Språk**: Python (3.11+)
-   **Miljö**: `venv` (Virtual Environment)
-   **API-orkestrering**: Responses API
-   **Versionshantering**: Git, GitHub API
-   **Utvecklingsmiljö**: Visual Studio Code

## Komma igång

Instruktioner för installation och konfiguration kommer inom kort. Processen kommer att innefatta:

1.  Kloning av detta repository.
2.  Installation av beroenden via `pip install -r requirements.txt`.
3.  Konfiguration av en `.env`-fil med nödvändiga API-nycklar (GitHub Token, OpenAI API Key, etc.).
4.  Upprättande av en GitHub App eller GitHub Action för att koppla boten till ditt repository.

## Bidra

Bidrag är välkomna! Vänligen skapa en "Issue" för att diskutera föreslagna ändringar eller öppna en Pull Request med en tydlig beskrivning av dina förbättringar.
