# ✍️ Multi-Agent Blog Writing Team

A multi-agent content pipeline where a supervisor agent orchestrates three 
specialist agents — researcher, fact-checker, and writer — to autonomously 
produce fact-checked blog posts, with a human-in-the-loop review step before 
final writing.


## What it does
- Enter any blog topic
- A **researcher** agent searches the web and compiles structured notes
- A **fact-checker** agent independently verifies the key claims
- You **review and optionally edit** the research before it goes further
- A **writer** agent drafts a full blog post using only verified information

## What makes this different from a single AI agent
Most AI agents use one model deciding which *tool* to call. This project goes 
a level deeper — a **supervisor agent** decides which *other agent* should act 
next, based on the current state of the work. Agents don't talk to each other 
directly; they all read and write to one shared state, and the supervisor 
routes the workflow.

                START
                  ↓
             SUPERVISOR  ←─────────────┐
            /    |     \               │
    researcher  fact_checker   writer  │
          │          │                 │
          └──────────┴─────────────────┘
          (loop back to supervisor until
           all steps are complete)
                  ↓
                 END


## Tech Stack
- **LangGraph** — Multi-agent orchestration and state management
- **Google Gemini 2.5 Flash** — LLM powering every agent
- **DuckDuckGo Search** — Free, no-API-key web search
- **Streamlit** — Web UI with human-in-the-loop review step

## Project Structure
blog-writing-team/

├── .env               # API keys (not uploaded to GitHub)

├── blog_team.py       # Agent definitions, shared state, graph wiring

├── app.py             # Streamlit UI with review/edit step

└── requirements.txt

## Setup & Installation

1. Clone the repository
```bash
   git clone https://github.com/yourusername/blog-writing-team
   cd blog-writing-team
```

2. Install dependencies
```bash
   pip install -r requirements.txt
```

3. Create a `.env` file in the root folder
   GEMINI_API_KEY=your_gemini_api_key_here

4. Run the app
```bash
   streamlit run app.py
```

## How to get API keys
- **Gemini API** — [Google AI Studio](https://aistudio.google.com)
- No key needed for search — DuckDuckGo is used directly

## Key Concepts Demonstrated

| Concept | Where it shows up |
|---|---|
| **Supervisor pattern** | One agent decides which specialist runs next |
| **Shared state** | All agents read/write to one `BlogState` object |
| **Conditional routing** | Graph edges change dynamically based on agent decisions |
| **Human-in-the-loop** | Pipeline pauses before writing for human review/edit |
| **State checkpointing** | LangGraph's `MemorySaver` persists progress across the pause |

## The Workflow in Detail

1. **Researcher** — Searches the web for the topic, synthesizes results into 
   structured notes with key facts and statistics
2. **Fact-Checker** — Extracts the most important claims from the research, 
   independently searches to verify each one, and labels them VERIFIED, 
   UNVERIFIED, or NEEDS CORRECTION
3. **Human Review** — The pipeline pauses here. You see the research and 
   fact-check report, and can edit the notes before continuing
4. **Writer** — Drafts a complete blog post, using only claims marked VERIFIED

## Note on Human-in-the-Loop
This project intentionally pauses before the writing step rather than running 
fully autonomously. This reflects a common real-world pattern — letting AI 
handle research and verification while keeping a human checkpoint before 
publishing content.

## Screenshots
<img width="1920" height="985" alt="Screenshot (1235)" src="https://github.com/user-attachments/assets/af85e10b-2280-4222-8a84-0ff9fcc4ce33" />
