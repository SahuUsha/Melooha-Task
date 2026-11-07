# Melooha -- Backend

A FastAPI backend for a personalized Vedic astrology question-answering
application. It combines retrieved knowledge from astrology reference
PDFs with user-specific birth-chart facts to generate grounded answers
with source citations.

## Features

-   **REST API:** FastAPI application with interactive OpenAPI
    documentation.
-   **Knowledge ingestion and retrieval:** Extracts text from PDF
    reference material, creates embeddings through the configured hosted
    embedding API, and retrieves relevant knowledge from PostgreSQL with
    `pgvector`.
-   **Grounded AI answers:** Uses Google Gemini 2.5 Flash as the primary
    generation model and Groq (`llama-3.3-70b-versatile`) as a fallback.
-   **Source citations:** Answers can cite the source document and page
    used during retrieval. Personal chart facts are handled separately
    from general reference knowledge.
-   **Personalized birth charts:** Calculates Vedic chart information
    using Swiss Ephemeris, Lahiri sidereal settings, and Whole Sign
    houses; chart facts can be stored and retrieved for personalized
    questions.
-   **Question credits:** Supports checking a user's question balance,
    adding credits, and viewing question history.
-   **Streaming responses:** Supports Server-Sent Events (SSE) for
    streaming answer generation.
-   **Automated tests:** Pytest tests cover health endpoints, user
    registration, credit operations, and question-history /
    insufficient-credit behavior.

## Technology stack

  ---------------------------------------------------------------------
  Area                               Technology
  ---------------------------------- ----------------------------------
  API                                Python, FastAPI, Uvicorn

  Data validation and configuration  Pydantic, pydantic-settings

  Database                           PostgreSQL (Neon-compatible),
                                     SQLAlchemy, Psycopg

  Vector search                      pgvector

  PDF processing                     PyMuPDF

  Embeddings                         Hosted Hugging Face embedding API,
                                     configured with `HF_TOKEN`

  LLM generation                     Gemini 2.5 Flash; Groq fallback

  Birth-chart calculations           Swiss Ephemeris

  Streaming                          Server-Sent Events (SSE)

  Testing                            Pytest, FastAPI TestClient
  ---------------------------------------------------------------------

## Project structure

``` text
Backend/
├── app/
│   ├── api/          # API route modules
│   ├── core/         # Application configuration
│   ├── db/           # Database connection and initialization
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic request/response schemas
│   ├── services/     # Retrieval, embeddings, PDFs, charts and answers
│   └── main.py       # FastAPI application entry point
├── tests/            # Automated API tests
├── .github/
│   └── workflows/
│       └── tests.yml # GitHub Actions test workflow
├── .env              # Local secrets (create this; do not commit)
├── .gitignore
├── pytest.ini
└── requirements.txt
```

## Prerequisites

-   Python 3.13 (the project has been tested with Python 3.13).
-   A PostgreSQL database with the `pgvector` extension available.
-   A Google Gemini API key.
-   A Hugging Face token for the configured embedding service.
-   A Groq API key if you want the fallback model enabled.
-   Git (for cloning the repository).

## Local setup

The commands below use Windows PowerShell. Run them from the directory
where you want the project.

### 1. Clone the repository

``` powershell
git clone https://github.com/SahuUsha/Melooha-Task.git
cd Melooha-Task
```

If your repository contains the backend at its root, continue from this
directory. If the backend is in a subdirectory, first `cd` into that
backend directory.

### 2. Create and activate a virtual environment

``` powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this for the current terminal
session and activate again:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

``` powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a file named `.env` in the backend project root (the same
directory as `requirements.txt`).

``` env
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@HOST:5432/DATABASE_NAME?sslmode=require
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_token
```

Replace each placeholder with your own value. For `DATABASE_URL`, use
the connection string supplied by your PostgreSQL provider, in the
format expected by SQLAlchemy and Psycopg. Remove any spaces from the
connection URL.

`GROQ_API_KEY` is optional in the application configuration; provide it
if you want the Groq fallback available. The other variables are
required by the current settings configuration.

**Keep credentials private:** - Never commit or push `.env`. - Do not
paste API keys into source files. - `.env` is included in
`.gitignore`. - For hosted deployments, configure secrets through the
hosting provider's environment-variable settings. - The GitHub Actions
test workflow uses dummy test values; real API credentials are not
needed for the current automated tests.

### 5. Prepare the database

Create/configure the PostgreSQL database and ensure the `vector`
extension required by pgvector is available:

``` sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Set `DATABASE_URL` to the database connection string. Run the database
initialization procedure provided in `app/db/` for this project before
using database-backed endpoints. Do not run the SQL statement above if
your database provider does not permit extension creation; enable
pgvector through the provider's database settings instead.

### 6. Start the API

From the backend project root, with the virtual environment activated:

``` powershell
python -m uvicorn app.main:app --reload
```

The local server should be available at:

-   API base URL: `http://127.0.0.1:8000`
-   Swagger UI: `http://127.0.0.1:8000/docs`
-   ReDoc: `http://127.0.0.1:8000/redoc`

Use `Ctrl+C` to stop the server. If port `8000` is already occupied,
stop the other process or choose another port, for example
`--port 8001`.

## API documentation and testing

FastAPI generates interactive API documentation from the application's
registered routes:

1.  Start the server.
2.  Open `http://127.0.0.1:8000/docs`.
3.  Expand an endpoint to inspect its method, path, request schema, and
    response.
4.  Use **Try it out** to send a request.

Run the automated tests from the backend project root:

``` powershell
python -m pytest -v
```

The current test suite contains 11 tests covering: - Home and health
endpoints. - User registration and duplicate-email handling. - Initial
question balance and balance lookup. - Adding question credits,
including invalid-user handling. - Question history, including
invalid-user handling. - Asking a question when the user has
insufficient credits.

The tests use a test database setup and dummy environment values. They
are intended to run without calling the live AI providers.

## Continuous integration

GitHub Actions runs the backend test suite on pushes and pull requests
to the `main` and `master` branches.

Workflow file:

``` text
.github/workflows/tests.yml
```

The workflow checks out the repository, sets up Python, installs
`requirements.txt`, and runs:

``` bash
python -m pytest -v
```

The current workflow uses dummy credentials for testing. Do not add
production API keys to the workflow unless a test genuinely requires
them.

## High-level request flow

1.  A client sends a request to the FastAPI backend.
2.  The API validates the request and checks the user's account and
    question-credit balance where applicable.
3.  For knowledge questions, the retrieval service searches relevant
    PDF-derived knowledge chunks using embeddings and vector similarity.
4.  For personalized questions, relevant stored birth-chart facts are
    also retrieved.
5.  The answer service builds a grounded prompt and calls Gemini; Groq
    is configured as a fallback.
6.  The response includes the available source citations. Streaming
    requests return answer content over SSE.
7.  Credit and history records are managed by the backend's database
    layer.

## Notes and limitations

-   This repository contains the backend. The frontend is maintained
    separately.
-   API route paths and request/response schemas may evolve; use `/docs`
    as the source of truth for the running version.
-   Do not assume every feature has a dedicated automated test. The 11
    current tests cover the cases listed above; chart calculations, live
    provider calls, streaming, retrieval quality, and fallback behavior
    should also be tested as the project evolves.
-   Keep reference PDFs and any private datasets out of Git unless you
    have permission to redistribute them and intentionally want them
    included.

## License

Add the license and attribution terms required by the project owner or
challenge instructions before publishing or redistributing this
repository.
