# Campus Customs: Shop + AI Chatbot (MGT 409, Homework 4)

An online storefront for official Yale merchandise with an AI shopping assistant, **Dan**.

- **Frontend:** React + Vite + TypeScript (`frontend/`).
- **Backend:** FastAPI (`backend/`), with a PydanticAI agent using `gpt-5.6-luna` through Portkey.
- **Data:** everything reads one SQLite database, `data/campus_customs.db`.

Customers can browse, search, filter and sort products, see live stock, add items to a cart, create an account and log in, and chat with Dan. Dan answers price and stock questions from the database, shows product cards, recommends products, understands follow-ups like "this one" or "the second one", and remembers logged-in customers' conversations.

## Repository layout

```
hw4/
├── AI_prompts.md          prompts used with the AI coding assistant, by problem
├── requirements.txt       backend Python dependencies
├── .env.example           template for the API key (copy to .env)
├── .gitignore
├── README.md
├── frontend/              Vite + React + TypeScript app
├── backend/
│   ├── main.py            FastAPI app (products, auth, chat, images)
│   ├── agent.py           PydanticAI agent: model, prompt, tools, per-request context
│   ├── tools.py           agent tools that read the catalogue and inventory
│   ├── models.py          Pydantic types for tool results, agent output and the API
│   ├── auth.py            account creation, login, sessions (Argon2id hashing)
│   ├── chat_history.py    saved chat history for logged-in customers
│   ├── audit.py           append-only agent audit trail
│   ├── db.py              database connection helper
│   └── prompts/prompt.md  the agent's system prompt and safety rules
└── output/
    ├── harness.md         full system documentation
    ├── design.md          Problem 10 design write-up
    ├── usability.md       Problem 9 usability improvements
    ├── app_check.html     Problem 11 live-site checks (open in a browser)
    ├── app_check_images/  screenshots used by app_check.html
    └── audit_trail.json   append-only log of agent runs
```

## 1. Place the data pack (not in this repository)

The database and product images come from the course data pack and are excluded from git. Put them here:

```
hw4/
└── data/
    ├── campus_customs.db
    └── products/          the product .jpg images
```

## 2. Add your API key

Create `.env` from the template in the `hw4/` folder, then open `.env` and replace the placeholder with your Portkey key:

```bash
cp .env.example .env
```

The key is only read from the environment. It is never written in the code.

## 3. Run the backend (FastAPI, port 8000)

Requirements: Python 3.11 or newer (developed with 3.14).

From the `hw4/` folder, the first time only, create the virtual environment:

```bash
python3 -m venv .venv
```

Then install the dependencies:

```bash
.venv/bin/python -m pip install --prefer-binary -r requirements.txt
```

Start the server from the `hw4/backend/` folder:

```bash
../.venv/bin/uvicorn main:app --reload --port 8000
```

Check that it is running: http://localhost:8000/api/health should return `{"status":"ok"}`. On Windows, use `.venv\Scripts\python` and `..\.venv\Scripts\uvicorn` instead.

## 4. Run the frontend (React + Vite, port 5173)

Requirements: Node.js 20.19+ or 22.12+ (required by Vite; developed with Node 24).

In a second terminal, from the `hw4/frontend/` folder, install the packages the first time:

```bash
npm install
```

Then start the dev server:

```bash
npm run dev
```

Open **http://localhost:5173**. The Vite dev server forwards `/api` and `/data` requests to the backend on port 8000, so both servers must be running.

## Using the site

- **Log in** with the seed test user from the course data pack (`test@campuscustoms.yale.edu`), or create a new account on **Create Account**.
- **Chat with Dan** using the "Ask Dan" button in the bottom-right corner. Try "Show me Yale hoodies", "How many Basic Hoodie Big Yale do you have in medium?" or "I need a Yale sweatshirt under $60". On a product page, ask "Do you have this in blue?".
- **Shop:** filter and sort on the Products page, pick a size on a product page, and review the cart.

Logged-in customers' chats are saved to the database. Guest chats last only for the current visit. Every agent run is appended to `output/audit_trail.json`, without message text or personal data.

## Documentation

See [`output/harness.md`](output/harness.md) for the full system overview: database schema, authentication, agent and tools, data models and why their fields were chosen, safety rules, the audit trail, limits and specs.
