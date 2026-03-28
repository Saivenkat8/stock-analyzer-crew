# Stock Analyzer Crew

A [CrewAI](https://crewai.com) project that runs a **two-agent pipeline** to research an **Indian listed stock** (NSE/BSE) and produce a structured **equity report**. The researcher gathers and organizes sources; the reporting analyst writes the final document and can run **deterministic valuation helpers** from your research numbers.

## What it does

1. **Researcher** — Resolves the correct listing when you pass a **company name or ticker**, searches the web with **Serper**, and compiles a **research pack**: fundamentals, technical context, news and sentiment, peers, and (when data exists) labeled inputs for valuation metrics—including guidance to use **broker research** (e.g. ICICI, HDFC, Nuvama, SBI and peers) for **forward estimates** such as **FY28** PAT/revenue where available, plus **screener** and **filings**-aligned **TTM** figures (e.g. **9MFY26 TTM** style anchors as defined in `tasks.yaml`).

2. **Reporting analyst** — Consumes that pack (via task `context`) and outputs a **360°-style report** (fundamentals, technicals, news/sentiment, key takeaways). It may call **`valuation_metrics_calculator`** when the pack includes the required numeric fields (trailing profit, forward profit, market cap, OCF, EBITDA, two revenue points, and optional custom `growth_period_years`).

Final markdown is written to **`output/report.md`**.

> **Disclaimer:** Outputs are for **informational** use only—not investment advice. Verify all numbers against **NSE/BSE**, company filings, and your broker. Model and search results can be wrong or outdated.

## Tech stack

- **Python** 3.10–3.13  
- **CrewAI** with **`crewai[tools,anthropic]`** (Claude for LLM calls)  
- **Tools:** [Serper](https://serper.dev) (Google search), custom **valuation metrics** tool (`src/research_crew/tools/valuation_metrics_tool.py`)  
- **Dependency manager:** [uv](https://docs.astral.sh/uv/) (used by `crewai install` / `crewai run`)

### Windows note

This repo pins **`lancedb==0.26.1`** via `[tool.uv] override-dependencies` in `pyproject.toml` because **newer `lancedb` wheels** used by the stack **omit `win_amd64`**, which otherwise breaks `uv sync` on Windows.

## Repository layout

| Path | Role |
|------|------|
| `src/research_crew/config/agents.yaml` | Agent roles, backstories, **`llm`** model ids |
| `src/research_crew/config/tasks.yaml` | Task descriptions, expected outputs, research/report structure |
| `src/research_crew/crew.py` | Wires agents, tasks, **Serper** + **valuation** tools, **`max_rpm`** throttling |
| `src/research_crew/main.py` | Run inputs: **`topic`** (stock name/ticker), **`current_year`** |
| `knowledge/` | Optional knowledge files for the crew |
| `.env.example` | Template for secrets (copy to **`.env`**) |

## Setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and ensure **Python** is available.

2. Clone the repo and enter the project root:

   ```bash
   cd research_crew
   ```

3. Install dependencies:

   ```bash
   crewai install
   ```

4. Copy **`.env.example`** to **`.env`** and set:

   - **`ANTHROPIC_API_KEY`** — [Anthropic console](https://console.anthropic.com/)  
   - **`SERPER_API_KEY`** — [Serper](https://serper.dev)  
   - **`MODEL`** (optional if each agent sets `llm` in `agents.yaml`) — e.g. `anthropic/claude-sonnet-4-20250514`

   Never commit **`.env`** (it is listed in **`.gitignore`**).

## Running

Set the stock under test in **`src/research_crew/main.py`** (`inputs['topic']`), then:

```bash
crewai run
```

Or:

```bash
uv run run_crew
```

The console prints the final result; the report file is **`output/report.md`**.

## Customization

- Change **models** in `agents.yaml` (`llm:` per agent).  
- Adjust **research depth, sources, and report sections** in `tasks.yaml`.  
- Tune **API rate limiting** in `crew.py` (`max_rpm` on the `Crew`).  
- Add tools in `crew.py` and implement them under `src/research_crew/tools/`.

## Further reading

- [CrewAI documentation](https://docs.crewai.com)  
- [Agents (YAML)](https://docs.crewai.com/concepts/agents)  
- [Tasks (YAML)](https://docs.crewai.com/concepts/tasks)

## License / project meta

Project structure originates from the CrewAI crew template; logic and prompts are customized for **Indian equity research** workflows.
