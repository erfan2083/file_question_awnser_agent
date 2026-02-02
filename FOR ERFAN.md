# For Erfan

A plain-language walkthrough of everything in this project -- the architecture, the technology choices, the bugs we ran into, the lessons we can take away, and how to think like an engineer who builds things that last.

---

## Table of Contents

1. [What Does This Project Actually Do?](#1-what-does-this-project-actually-do)
2. [The Story of How It Was Built](#2-the-story-of-how-it-was-built)
3. [The Architecture: Why We Structured It This Way](#3-the-architecture-why-we-structured-it-this-way)
4. [The Multi-Agent System: How the AI Brain Works](#4-the-multi-agent-system-how-the-ai-brain-works)
5. [How the Pieces Connect: A Request's Journey](#5-how-the-pieces-connect-a-requests-journey)
6. [The Technology Choices and Why We Made Them](#6-the-technology-choices-and-why-we-made-them)
7. [The Bugs We Fought and What They Taught Us](#7-the-bugs-we-fought-and-what-they-taught-us)
8. [Lessons in Engineering Thinking](#8-lessons-in-engineering-thinking)
9. [Best Practices Worth Internalizing](#9-best-practices-worth-internalizing)
10. [What You Could Build Next](#10-what-you-could-build-next)

---

## 1. What Does This Project Actually Do?

Imagine you have a stack of documents -- PDFs, Word files, plain text, even photos of printed pages. You want to ask questions about them in plain English (or Persian) and get accurate answers with citations pointing to exactly which document and page the answer came from.

That is what this system does. You upload documents, it reads and understands them, and then you can have a conversation with your documents like they are a knowledgeable assistant who has memorized everything in them.

But under the hood, it is not one monolithic program. It is a **team of AI agents**, each with a specific job, passing work between them like a relay race. One agent figures out what you are asking. Another searches through your documents. A third writes the answer. And a fourth handles special tasks like summarizing or translating entire documents.

---

## 2. The Story of How It Was Built

This is worth telling because no real project arrives fully formed. They evolve, they fail, they get rewritten. This one went through **five major versions in six weeks**, and that journey is more instructive than the final code.

### Version 1: The Quick Prototype (October 11-18, 2025)

The first version was deliberately simple: FastAPI for the backend, Streamlit for the frontend, OpenAI for the LLM, and FAISS for vector storage. Thirteen dependencies. It could upload a file, split it into chunks, embed the chunks, and answer questions.

This is how experienced developers work: **build the simplest thing that works first**. Don't worry about architecture, scalability, or clean code. Just prove the concept. Can we upload a document, search through it, and get a reasonable answer? Yes? Good. Now we know it is worth building properly.

### Version 2: The Architecture Shift (October 20, 2025)

V2 was built in a single day. It introduced the LangGraph multi-agent system (the core idea that survived into the final version), switched from a simple Streamlit interface to React, and added hybrid retrieval (vector search + keyword search combined). It even tried running a local HuggingFace LLM (Phi-3 with 8-bit quantization) instead of calling an API.

The local LLM was ambitious but impractical -- it needed serious GPU resources. This was the first lesson: **know the deployment environment before choosing your tools**. A local model sounds great for privacy and cost, but if you are running in Docker containers on a VPS, you need an API-based model.

### Version 3: The Failed Experiment (November 7-15, 2025)

V3 was a proper Python package with `pyproject.toml`, individual agent modules, and structured documentation. The commit message tells the whole story: "v3 failed to test." It got too complicated before it got working. The next commit was just adding a `.gitignore`.

This is one of the most common traps in software engineering: **building the scaffolding before the building**. V3 had project status reports, completion checklists, and architectural documentation, but it did not run. Tests matter more than documents about tests.

### Versions 4 and 5: Finding the Right Stack (November 15-18, 2025)

Erfan pivoted to Django (a more opinionated, batteries-included framework), switched from OpenAI to Google Gemini, replaced FAISS with PostgreSQL + pgvector, and built both v4 and v5 in parallel. V5 won. The commit message: "v5 is the best."

The switch to Django was practical. Django has a mature admin panel, ORM, migration system, and DRF (Django REST Framework) for APIs. When you are building a full-stack application with a database, file uploads, and multiple API endpoints, Django gives you a lot for free. FastAPI is elegant for microservices, but Django is a powerhouse for applications.

### The Hexagonal Refactoring (November 26-27, 2025)

V5 worked but its code was tangled -- business logic mixed with Django ORM calls, no clear boundaries between layers. The hexagonal architecture refactoring separated everything into clean layers (we will cover this in detail below). This was the single most significant architectural change in the project: 5,121 lines added across 58 files.

### The Docker Wars (November 27, 2025)

Immediately after the refactoring, Docker builds broke. Five separate fixes were needed in rapid succession. More on this in the bugs section -- it is one of the best learning experiences in the whole project.

---

## 3. The Architecture: Why We Structured It This Way

### The Hexagonal Architecture (a.k.a. Ports and Adapters)

Think of this architecture like a company:

- **The CEO (Domain Layer)** makes business decisions. They do not care whether the company uses Slack or email, PostgreSQL or MongoDB. They think in pure business terms: "A document can go from UPLOADED to PROCESSING, but never from READY back to UPLOADED."

- **The Management Team (Application Layer)** coordinates work. They know *what* needs to happen but not *how*. "We need to upload a document, process it into chunks, generate embeddings, and save them." They define the job descriptions (interfaces) but do not hire specific people.

- **The Workers (Infrastructure Layer)** do the actual work with specific tools. "I will use Django ORM to save this to PostgreSQL." "I will call the Gemini API to generate this embedding." They are replaceable -- you could swap one worker for another as long as they can do the same job.

- **The Reception Desk (API Layer)** handles incoming requests from the outside world. They translate HTTP requests into something the management team understands, and format the responses back into HTTP.

Here is what this looks like in the codebase:

```
backend/core/
  domain/              <-- The CEO: pure business rules, zero framework imports
    entities/          <-- Document, DocumentChunk, ChatSession, ChatMessage
    value_objects/     <-- DocumentStatus, FileType, Embedding
    exceptions.py      <-- Business rule violations

  application/         <-- Management: use cases and interfaces
    use_cases/         <-- UploadDocument, ProcessDocument, AskQuestion
    dto/               <-- Data Transfer Objects (the memos between layers)
    ports/             <-- Interfaces (job descriptions for workers)

  infrastructure/      <-- Workers: concrete implementations
    adapters/
      repositories/    <-- Django ORM implementations
      services/        <-- Gemini API, PDF extraction, etc.
      rag/             <-- LangGraph RAG orchestrator

  dependencies.py      <-- The HR department: wires everyone together
```

### Why This Matters

The **domain layer has zero framework imports**. Open `core/domain/entities/document.py` and you will not find a single `import django` anywhere. It is pure Python dataclasses and enums. This means:

1. **You can test business logic without a database.** Just create a `Document` dataclass and call `start_processing()` on it. No Django, no PostgreSQL, no network.

2. **You can swap frameworks.** If you wanted to migrate from Django to FastAPI tomorrow, your business logic would not change at all. You would only rewrite the infrastructure layer.

3. **The code tells you what matters.** When you read the domain layer, you see the *business rules* of the application, undiluted by technical plumbing.

Look at this state machine in `DocumentStatus`:

```python
def can_transition_to(self, new_status: 'DocumentStatus') -> bool:
    valid_transitions = {
        self.UPLOADED: [self.PROCESSING, self.FAILED],
        self.PROCESSING: [self.READY, self.FAILED],
        self.READY: [],                    # Terminal -- no going back
        self.FAILED: [self.PROCESSING]     # Can retry
    }
    return new_status in valid_transitions.get(self, [])
```

This is a business rule expressed in the purest possible way. A document that is `READY` cannot go back to `PROCESSING`. A `FAILED` document can be retried. These rules live in the domain, not buried inside some Django view where they would be mixed with HTTP handling, serialization, and error formatting.

### The Dependency Injection Container

The `DependencyContainer` in `core/dependencies.py` is the wiring diagram. It creates all the concrete implementations and plugs them into the use cases:

```python
self.upload_document_use_case = UploadDocumentUseCase(
    document_repository=self.document_repository   # <-- DjangoDocumentRepository
)
```

The `UploadDocumentUseCase` does not know it is getting a Django repository. It only knows it is getting something that implements `DocumentRepository` (the interface). In tests, you could pass a `FakeDocumentRepository` that stores everything in a dictionary. Same use case, different implementation.

This is the **Dependency Inversion Principle** -- the "D" in the SOLID principles. High-level modules (use cases) do not depend on low-level modules (Django ORM). Both depend on abstractions (interfaces).

---

## 4. The Multi-Agent System: How the AI Brain Works

### The Assembly Line Analogy

Imagine an automotive factory. A car does not get built by one person doing everything. There is a station for the frame, a station for the engine, a station for painting, and so on. Each station is specialized, and the car moves from one to the next.

Our RAG system works the same way:

```
User's Question
      |
      v
[Router Agent]  -- "What kind of question is this?"
      |
      +--> RAG_QUERY -----> [Retriever Agent] --> [Reasoning Agent] --> Answer + Citations
      |
      +--> SUMMARIZE -----> [Utility Agent] --> Summary
      +--> TRANSLATE -----> [Utility Agent] --> Translation
      +--> CHECKLIST -----> [Utility Agent] --> Checklist
```

This is implemented using **LangGraph**, which lets you define a workflow as an actual graph -- nodes (agents) and edges (connections). The state (everything we know so far) gets passed from node to node:

```python
class AgentState(TypedDict):
    query: str                           # What the user asked
    chat_history: List[Dict[str, str]]   # Previous messages
    intent: str                          # What kind of question (RAG_QUERY, SUMMARIZE, etc.)
    retrieved_chunks: List[Dict]         # Relevant document fragments
    answer: str                          # The final answer
    citations: List[Dict]               # Where the answer came from
    metadata: Dict                       # Extra info (agent type, timing, etc.)
    error: str                          # What went wrong (if anything)
```

### Agent 1: The Router

The Router is the triage nurse. It looks at your question and decides who should handle it. Right now it uses keyword matching (looking for words like "summarize", "translate", "checklist" in English and Persian), but this could be upgraded to use an LLM classifier for more nuanced intent detection.

```python
if any(keyword in query for keyword in ["summarize", "summary", "خلاصه"]):
    state["intent"] = "SUMMARIZE"
```

This is a deliberate simplicity. Keyword matching is fast, cheap, and predictable. An LLM-based router would be more flexible but also slower, more expensive, and harder to debug. The engineering judgment here was: **start with the simplest approach that works, upgrade when it is not enough.**

### Agent 2: The Retriever (The Detective)

This is the most technically interesting agent. It finds the most relevant chunks of text from your documents. But it does not just do one kind of search -- it does two and combines them.

**Vector Search (Semantic):** Converts your question into a 768-dimensional vector (using Gemini's embedding model) and finds chunks whose vectors point in similar directions. This catches paraphrases and conceptual matches. If you ask "What are the revenue figures?" it will find chunks about "income," "earnings," and "financial results" even if they never use the word "revenue."

**BM25 Search (Keyword):** A classic information retrieval algorithm that ranks documents by keyword frequency, weighted by how rare the keywords are. If you ask about "NVIDIA quarterly earnings Q3 2024," the vector search might get confused by all the general finance documents, but BM25 will zero in on chunks containing those exact terms.

**Hybrid Combination:** The two scores get normalized (scaled to 0-1) and combined:

```
final_score = 0.7 * vector_score + 0.3 * bm25_score
```

The 70/30 weighting says: "Trust the semantic understanding more, but do not ignore exact keyword matches." This ratio was a tuning decision -- you could adjust it based on your use case. Legal document search might want more keyword weight (0.5/0.5) because exact terminology matters. Casual Q&A might want more semantic weight (0.8/0.2).

### Agent 3: The Reasoner (The Writer)

The Reasoner takes the retrieved chunks, combines them into a context block, includes the last 2 exchanges of chat history for continuity, and asks Gemini to generate an answer. The prompt is carefully structured:

1. "Answer based ONLY on the provided context" -- prevents hallucination
2. "If the context does not contain enough information, say so" -- honest uncertainty
3. "Include specific references" -- enables citation generation
4. Recent chat history -- enables follow-up questions ("What about the second quarter?" after asking about Q1)

### Agent 4: The Utility Agent (The Specialist)

The Utility Agent handles non-question tasks: summarizing documents, translating between English and Persian, and creating checklists. It has a special path (`process_document_utility`) that bypasses the router entirely and feeds it the full document content directly -- because when you click "Summarize" on a document in the sidebar, you do not want the router trying to classify "summarize" as a RAG query.

### Why LangGraph Instead of Just Sequential Functions?

You could implement this same flow with plain function calls: `result = reasoner(retriever(router(query)))`. So why use LangGraph?

1. **Conditional routing is explicit.** The graph structure makes it clear that the Router can send work to *either* the Retriever or the Utility agent, and that is visible in the graph definition, not hidden in if/else branches.

2. **State management is typed.** `AgentState` is a `TypedDict`, so every agent knows exactly what data is available. No passing around generic dictionaries and hoping keys exist.

3. **It scales.** When you want to add a new agent (say, a fact-checker that runs between the Reasoner and the output), you add a node and an edge. You do not restructure the whole pipeline.

4. **It is debuggable.** You can inspect the state after each node. You can visualize the graph. You can trace exactly which path a query took.

---

## 5. How the Pieces Connect: A Request's Journey

Let us trace what happens when a user asks "What were the Q3 revenue figures?" from button click to answer on screen.

### Step 1: The Frontend (React)

The user types the question in `ChatInterface.js` and hits Send. The component calls:

```javascript
chatApi.sendMessage(sessionId, "What were the Q3 revenue figures?")
```

This is an Axios POST to `http://localhost:8000/api/chat/sessions/5/messages/` with `{content: "What were the Q3 revenue figures?"}`.

### Step 2: The API Layer (Django REST Framework)

The request hits `ChatSessionViewSet.messages()` in the backend. The view:
1. Validates the request body
2. Loads the chat session and its history (previous messages)
3. Creates the `RAGOrchestrator` and calls `process_query(query, chat_history)`

### Step 3: The LangGraph Pipeline

The orchestrator kicks off the graph:

1. **Router Agent** scans the query. No summary/translate/checklist keywords found, so `intent = "RAG_QUERY"`.

2. **Retriever Agent** generates a query embedding by calling Gemini's embedding API. Then it loads ALL chunks from all READY documents, runs both vector search and BM25 search, combines the scores with alpha=0.7, and returns the top 5 chunks.

3. **Reasoning Agent** builds a prompt with the retrieved chunks as context, includes recent chat history, and calls Gemini's chat API. It gets back an answer and generates citations from the retrieved chunks.

### Step 4: The Response

The view saves both the user message and the assistant message to the database, attaches citations as metadata, and returns a JSON response:

```json
{
  "answer": "According to the Q3 financial report...",
  "citations": [
    {
      "document_title": "Q3 Financial Report.pdf",
      "page": 12,
      "snippet": "Total revenue for Q3 2024 reached..."
    }
  ],
  "metadata": {"agent_type": "reasoning", "num_retrieved": 5}
}
```

### Step 5: Back to the Frontend

React Query's `onSuccess` callback fires. It adds both the user message and the AI response to the local message array. The chat interface re-renders, showing the answer with expandable citation cards.

### The Key Insight

Notice how each layer speaks a different language:
- The **frontend** speaks HTTP and JSON
- The **API layer** speaks Django serializers and view methods
- The **application layer** speaks use cases and DTOs
- The **domain layer** speaks pure business objects
- The **infrastructure layer** speaks Gemini API calls and SQL queries

Each layer translates between its language and the next. This is what clean architecture looks like in practice -- each layer has one job and a clear boundary.

---

## 6. The Technology Choices and Why We Made Them

### Django + DRF (instead of FastAPI)

The project started with FastAPI (v1 and v2). We switched to Django because:

- **File uploads and media management** -- Django's `FileField` and media serving is battle-tested.
- **ORM and migrations** -- Writing raw SQL or using SQLAlchemy with Alembic is more work for less safety.
- **Admin panel** -- Free CRUD interface for debugging data issues.
- **DRF** -- ViewSets, serializers, pagination, filtering -- all production-ready.

FastAPI is the better choice for small, focused APIs (microservices, ML model serving). Django is the better choice for full applications with a database, file handling, and admin needs.

### PostgreSQL + pgvector (instead of FAISS or a dedicated vector DB)

FAISS (v1-v3) stores vectors in memory. Fast, but:
- No persistence without extra work (serializing to disk)
- No relational queries (you cannot join vectors with document metadata)
- Runs in-process (cannot scale independently)

pgvector gives us vectors *inside PostgreSQL*, which means:
- Vectors and metadata live together (no sync issues)
- ACID transactions (if the document save fails, the chunks do not get orphaned)
- Standard SQL for everything (no learning a separate query language)
- One database to operate (not two)

The tradeoff: pgvector is slower than FAISS or specialized vector databases (Qdrant, Pinecone, Weaviate) at very large scale (millions of vectors). For this project's scale (thousands to tens of thousands of chunks), PostgreSQL is more than enough, and the operational simplicity is worth it.

### Google Gemini (instead of OpenAI)

The project started with OpenAI (v1) and even tried local HuggingFace models (v2). We settled on Gemini because:
- **Multimodal** -- Gemini can process images directly, which is useful for OCR on uploaded photos.
- **Generous free tier** -- Good for development and testing.
- **Task-specific embeddings** -- Gemini's embedding API lets you specify `task_type="retrieval_document"` vs `task_type="retrieval_query"`, which produces better embeddings for search.

The VPN/geo-blocking issue (more in the bugs section) required forcing REST transport instead of the default gRPC:

```python
genai.configure(
    api_key=settings.GOOGLE_API_KEY,
    transport='rest',
    client_options=client_opts
)
```

### UV Package Manager (instead of pip)

UV is Rust-powered and dramatically faster than pip. But the real win is **reproducibility**: `uv.lock` locks every dependency to an exact version, so `uv sync --frozen` installs the exact same packages every time. With pip, `requirements.txt` can drift (version ranges resolve differently on different days), and you end up with "works on my machine" bugs.

### React + React Query (instead of Streamlit or raw React)

Streamlit is great for prototyping ML apps but poor for production UIs (limited layout control, no state management, full-page rerenders). React gives us:
- Component-based architecture
- Fine-grained state management
- React Query for server state caching and automatic revalidation

The React Query integration is particularly elegant. Look at the document list polling:

```javascript
refetchInterval: (data) => {
    const hasProcessing = data?.some(doc => doc.status === 'PROCESSING');
    return hasProcessing ? 3000 : false;
}
```

This says: "If any document is still processing, check every 3 seconds. Otherwise, stop polling." Smart polling that adapts to the current state.

### Docker Compose (for orchestration)

Three services that need to start in a specific order, share a network, and persist data. Docker Compose makes this a single `docker-compose up`. The health check on PostgreSQL ensures the backend does not try to migrate before the database is ready.

---

## 7. The Bugs We Fought and What They Taught Us

This is the most valuable section. Every bug here is a lesson about something non-obvious.

### Bug 1: The Hatchling Discovery Failure

**What happened:** After switching to UV (which uses hatchling as its build backend), Docker builds failed with an error about not knowing which packages to include.

**Why:** Hatchling, unlike setuptools, does not auto-discover packages. It needs to be told explicitly which directories are Python packages.

**The fix:** Added this to `pyproject.toml`:
```toml
[tool.hatch.build.targets.wheel]
packages = ["api", "chat", "config", "core", "documents", "evaluation", "rag"]
```

**The lesson:** When you change build tools, do not assume the new tool works the same way as the old one. Read the migration guide. Every build system has opinions, and you need to understand them.

### Bug 2: Docker Build Order -- The Chicken-and-Egg Problem

**What happened:** The Dockerfile was written to optimize layer caching:
```dockerfile
COPY pyproject.toml uv.lock ./    # Copy deps first
RUN uv sync --frozen              # Install deps (cached if deps unchanged)
COPY . .                          # Copy source code
```

This is the standard Docker pattern: copy dependency files first, install them, then copy source code. This way, `uv sync` is cached unless `pyproject.toml` changes.

But it failed. Hatchling needed the actual source directories to exist *during* `uv sync` because it was also trying to build the project package.

**The fix:** Copy the source directories *before* running `uv sync`:
```dockerfile
COPY pyproject.toml uv.lock ./
COPY api/ api/
COPY chat/ chat/
COPY core/ core/
# ... all other packages
RUN uv sync --frozen
COPY . .
```

**The lesson:** Docker layer caching is an optimization. When it conflicts with build requirements, correctness wins. Also: understand what your build tool *actually does* during install. UV with hatchling does not just install dependencies -- it also resolves the local package, which needs source files.

### Bug 3: The Missing README

**What happened:** Hatchling requires any file referenced in `pyproject.toml` metadata to exist during build. `readme = "README.md"` was in the config, but `README.md` did not exist.

**The fix:** Create the file.

**The lesson:** This is the kind of bug that takes 30 seconds to fix but 30 minutes to diagnose. The error message was not "README.md not found" -- it was a cryptic hatchling build error. When you see a build failure, read the *full* error message, not just the last line. And when configuring a build tool, make sure every referenced file exists.

### Bug 4: The pgvector Extension

**What happened:** Django migrations failed because the `vector` column type did not exist. PostgreSQL did not have the pgvector extension enabled.

**The fix:** Created `init-db.sql`:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
And mounted it into the container's initialization directory:
```yaml
volumes:
  - ./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
```

**The lesson:** PostgreSQL extensions are not installed by default, even in images that include them. The `pgvector/pgvector:pg16` Docker image has the extension *available*, but each database still needs to `CREATE EXTENSION` explicitly. Always check initialization requirements for database features.

Also: this init SQL only runs when the database is first created. If you already have a `postgres_data` volume, adding the init script will not retroactively run it. You would need to `docker-compose down -v` and recreate.

### Bug 5: The .venv Symlink Issue (Windows)

**What happened:** Docker builds failed on Windows because the local `.venv` directory contained symlinks that Docker could not copy.

**The fix:** Added a `.dockerignore` file:
```
.venv/
__pycache__/
*.pyc
.env
.git/
```

**The lesson:** `.dockerignore` is not optional. Without it, Docker copies *everything* in the build context into the image, including things that should never be in a container (virtual environments, IDE settings, git history, `.env` files with secrets). Always create a `.dockerignore` at the start of a project, not after the first failure.

### Bug 6: The Port Wars (The Most Entertaining Bug)

**What happened:** Port configuration for the backend was specified in **four different places**:
1. The Django `runserver` command (what port Django listens on *inside* the container)
2. The Dockerfile `EXPOSE` directive (documentation, not functional)
3. The `docker-compose.yml` `ports` mapping (what port maps from host to container)
4. The frontend `REACT_APP_API_URL` (where the browser sends requests)

These four values went in and out of sync at least four times across the project's history. At one point, Django was listening on port 9000, the compose mapping was `9000:8000`, and the frontend was pointing at `localhost:8000`. Nothing could talk to anything.

**The fix (final):** Standardize everything to port 8000:
- Django: `runserver 0.0.0.0:8000`
- Compose ports: `8000:8000`
- Frontend: `REACT_APP_API_URL=http://localhost:8000`

**The lesson:** This is a **configuration drift** bug. When the same value is defined in multiple places, they *will* get out of sync. The more places a value is defined, the more likely it is to break.

Good practice: define the value in **one place** and derive it everywhere else. For example, use an environment variable in `docker-compose.yml` and reference it in both the command and the port mapping:

```yaml
environment:
  - PORT=8000
command: sh -c "runserver 0.0.0.0:${PORT}"
ports:
  - "${PORT}:${PORT}"
```

This way you change it in one place and everything updates.

### Bug 7: The Utility Agent's Empty Plate

**What happened:** When you clicked "Summarize" on a document in the sidebar, the utility agent received the user's short query text ("summarize this document") instead of the actual document content. The summary was a summary of the word "summarize."

**The fix:** Created `process_document_utility()`, a dedicated method that:
1. Loads all chunks for the specific document
2. Concatenates them into full text
3. Bypasses the router and calls the utility agent directly with the full text

**The lesson:** When an action operates on *data*, not on a *question*, it needs a different code path. The router/retriever/reasoner pipeline is designed for questions ("What does document X say about Y?"). Utility actions ("Summarize document X") need direct access to the document, not a search result. Recognizing when an existing pipeline does not fit a new use case -- and building a dedicated path -- is a key engineering skill.

### Bug 8: The 415 Unsupported Media Type

**What happened:** The new `/utility/` endpoint returned HTTP 415. The frontend was sending JSON, but the `DocumentViewSet` only accepted `MultiPartParser` and `FormParser` (needed for file uploads). It was rejecting JSON requests.

**The fix:** Added `JSONParser` to the ViewSet's `parser_classes`:
```python
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class DocumentViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
```

**The lesson:** DRF ViewSets have a single `parser_classes` that applies to *all* actions in the ViewSet. When you add a new action that accepts a different content type than existing actions, you need to update the parser list. The alternative (better for complex cases) is to use `get_parsers()` to return different parsers per action:

```python
def get_parsers(self):
    if self.action == 'utility':
        return [JSONParser()]
    return [MultiPartParser(), FormParser()]
```

---

## 8. Lessons in Engineering Thinking

### Lesson 1: Iterate, Don't Architect Prematurely

This project went through five versions. That is not failure -- that is learning. V1 proved the concept. V2 proved the multi-agent approach. V3 proved that over-architecture kills momentum. V4 and V5 found the right technology stack. The hexagonal refactoring cleaned it up.

The wrong approach would have been to spend two weeks designing the perfect architecture before writing a line of code. The right approach was to build, learn, and refine. As Fred Brooks wrote: "Plan to throw one away; you will, anyhow."

### Lesson 2: The State Machine Pattern

The `DocumentStatus` state machine (`UPLOADED -> PROCESSING -> READY/FAILED`) is a small piece of code with disproportionate value. Without it, you might accidentally:
- Try to process a document that is already being processed
- Query chunks from a document that is not ready
- Mark a ready document as uploaded again

State machines make invalid states unrepresentable. They turn runtime bugs into compile-time (or at least test-time) errors. Whenever you have an entity that moves through stages, write a state machine.

### Lesson 3: Don't Fight the Framework

V1-V3 used FastAPI, which is great for APIs but requires you to bring your own ORM, migration tool, admin interface, and file handling. Django provides all of these. The lesson is not "Django is better than FastAPI" -- it is "choose the tool that gives you the most of what you need for free."

If this were a stateless microservice that just proxied LLM calls, FastAPI would be the better choice. But we need a database with migrations, file uploads with persistence, and an admin panel for debugging. Django was designed for exactly this.

### Lesson 4: Hybrid Search Is Better Than Either Alone

Pure vector search fails on exact terms (names, numbers, specific jargon). Pure keyword search fails on paraphrases and conceptual matches. Combining them covers both weaknesses:

- "NVIDIA" (a proper noun) gets boosted by BM25
- "earnings" vs "revenue" vs "income" (synonyms) gets caught by vectors
- Combined: best of both worlds

This is a general principle: **ensemble methods almost always outperform single methods.** In ML, in search, in testing, in code review -- multiple perspectives catch what a single perspective misses.

### Lesson 5: Understand Your Deployment Environment

The local HuggingFace model (Phi-3, v2) was theoretically great: no API costs, no network dependency, full privacy. Practically, it needed a GPU, which the Docker deployment did not have. The VPN/geo-blocking issue with Gemini required switching to REST transport. These are not code problems -- they are environment problems. And they can only be caught by *actually running the code in the target environment*, not by looking at it in an IDE.

### Lesson 6: Separation of Concerns Is Not Just Theory

The hexagonal architecture is not academic indulgence. Here is a concrete example:

When the Gemini API changed how embeddings worked, only `GeminiEmbeddingService` needed to change. Not the use cases. Not the domain. Not the API layer. Not the tests for any of those layers.

When the utility endpoint needed a JSON parser, only the API layer changed. The domain did not know or care.

When you need to add a new file type (say, EPUB), you create one new `EPUBTextExtractor` class, add it to the dependency container, and nothing else changes.

Each change is localized. You do not need to understand the entire system to make a change safely. This is what good architecture buys you.

### Lesson 7: Error Messages Are a Feature

Look at the error handling in the RAG orchestrator:
```python
except Exception as e:
    print(f"Retriever Agent Error: {str(e)}")
    state["error"] = f"Retrieval error: {str(e)}"
    state["retrieved_chunks"] = []
```

Every agent catches exceptions, logs them, sets them in state, and returns a safe default. The error propagates through the state, not through exception unwinding. This means:
- The graph does not crash
- The user gets a meaningful error message
- The logs show where the error occurred
- Downstream agents can check `state["error"]` and adapt

---

## 9. Best Practices Worth Internalizing

### 1. Read Code Before Writing Code

Before modifying any file, read it first. Understand what is already there. The fastest way to introduce bugs is to make assumptions about code you have not read.

### 2. One Change, One Commit

Each commit in the good parts of this project's history does one thing. "Fix 415 error on utility endpoint" -- that is one commit. "Add hexagonal architecture" -- that is one commit (a big one, but still one logical change). When something breaks, you can `git bisect` to find exactly which commit caused it.

### 3. Tests as Documentation

The test files in `backend/tests/` are arguably the best documentation in the project. `test_domain.py` shows you exactly how domain entities are supposed to behave. `test_chat.py` shows you exactly how the API is supposed to respond. When in doubt about how something works, read the tests.

### 4. Docker-First Development

Always develop with Docker from day one, even if it seems like overhead. The port wars bug, the pgvector extension bug, the `.venv` symlink bug -- all of these would have been caught earlier if Docker was the primary development environment from the start.

### 5. Make Invalid States Unrepresentable

The `DocumentStatus` state machine is a great example. Other examples:
- Use enums instead of strings for finite sets of values
- Use `Optional[X]` instead of `X` when a value might not exist
- Use `TypedDict` instead of `Dict[str, Any]` when you know the shape

### 6. Log at Boundaries

The RAG orchestrator logs at the entry and exit of each agent, and at every exception. When something goes wrong in production, these logs are your only window into what happened.

### 7. Configuration Belongs in One Place

Environment variables in `docker-compose.yml`, read by Django `settings.py`, accessed through `settings.CHUNK_SIZE`. One source of truth. Not hardcoded in three different files.

### 8. Start Simple, Add Complexity When Needed

The router uses keyword matching instead of an LLM classifier. The vector search iterates through all chunks instead of using an approximate nearest neighbor index. The evaluation system uses Jaccard similarity instead of embedding-based comparison. These are all "good enough for now" decisions that kept the codebase simple while delivering working functionality. You can always optimize later -- and you will know *where* to optimize because you will have metrics.

---

## 10. What You Could Build Next

If you want to keep growing this project, here are paths ordered by learning value:

### Add Celery for Background Processing
Right now, document processing is synchronous -- the upload request blocks until processing is done. For large documents, this can time out. Adding Celery (a distributed task queue) with Redis as a broker would let you return immediately from the upload and process in the background. This teaches you about **async task processing**, **message queues**, and **worker patterns**.

### Add User Authentication
Right now, all documents and chat sessions are global. Adding Django's authentication system with JWT tokens would give each user their own documents and chat history. This teaches you about **authentication/authorization**, **multi-tenancy**, and **API security**.

### Upgrade the Router to Use an LLM
Replace the keyword-matching router with a Gemini call that classifies intent. This teaches you about **prompt engineering for classification**, **few-shot learning**, and the tradeoffs between rule-based and ML-based approaches.

### Add WebSocket Support for Streaming
Instead of waiting for the full answer, stream tokens as they are generated. This teaches you about **WebSockets**, **Django Channels**, **server-sent events**, and **real-time communication**.

### Build a Proper Evaluation Pipeline
Add more sophisticated metrics: BLEU score, ROUGE score, embedding-based similarity (instead of Jaccard), and human evaluation workflows. This teaches you about **ML evaluation**, **measurement**, and **continuous quality monitoring**.

### Add Semantic Chunking
Instead of splitting documents at fixed character boundaries, use embeddings to detect topic boundaries and split there. This teaches you about **text segmentation**, **embedding geometry**, and how chunk quality affects retrieval quality.

---

## Final Thought

Software engineering is not about writing code. It is about making decisions under uncertainty, learning from failures, and building systems that can evolve. This project is a small example of that -- from a 13-dependency prototype to a hexagonal architecture with multi-agent AI, each version taught something the previous one could not.

The best code in this project is not the cleverest code. It is the `DocumentStatus.can_transition_to()` method -- seven lines that prevent an entire class of bugs. It is the `DependencyContainer` that makes every component swappable. It is the hybrid retrieval that combines two imperfect approaches into something better than either.

Keep building. Keep breaking things. Keep rewriting. That is how you get good.
