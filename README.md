# Survivor Network

A graph-based analytics and communication platform for survivor communities, powered by Google Cloud Spanner and Vertex AI.

## Overview

Survivor Network combines a React frontend with a FastAPI backend to provide visualize relationships between survivors, skills, and resources. It features an AI-powered chat interface that allows users to query the graph database using natural language.

## Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **Google Cloud Platform**:
  - Cloud Spanner Instance
  - Vertex AI API enabled (for AI features)
- **Google Cloud Credentials**: A service account key JSON file.

## Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Install dependencies with uv:**
    Make sure you have [uv installed](https://github.com/astral-sh/uv).
    ```bash
    uv sync
    ```

3.  **Configuration:**
    - Create a `.env` file in the `backend` directory (see [Environment Variables](#environment-variables)).
    - Place your Google Cloud service account key (e.g., `spanner-key.json`) in the project root or backend directory and reference it in `.env`.

4.  **Initialize the Database:**
    Run the script to populate Spanner with initial sample data.
    ```bash
    uv run python create_property_graph.py
    ```

5.  **Run the Server:**
    ```bash
    uv run uvicorn main:app --reload
    ```
    The backend API will be available at `http://localhost:8000`.

## Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Configuration:**
    - Create a `.env` file in the `frontend` directory based on `.env.example`.

4.  **Run the Development Server:**
    ```bash
    npm run dev
    ```
    The application will be accessible at `http://localhost:5173`.

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `PROJECT_ID` | GCP Project ID | `your-project-id` |
| `INSTANCE_ID` | Spanner Instance ID | `survivor-instance` |
| `DATABASE_ID` | Spanner Database ID | `survivor-db` |
| `GRAPH_NAME` | Spanner Graph Name | `SurvivorGraph` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key | `../spanner-key.json` |
| `LOCATION` | Vertex AI Location | `us-central1` |
| `USE_MEMORY_BANK` | Enable Memory Bank agent | `True` |

### Frontend (`frontend/.env`)

| Variable | Description | Default |
| :--- | :--- | :--- |
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_WS_URL` | Backend WebSocket URL | `ws://localhost:8000` |

## Project Structure

```
survivor-network/
├── backend/            # FastAPI Backend
│   ├── agent/          # AI Agent logic
│   ├── api/            # API Routes
│   ├── models/         # Pydantic Models
│   ├── services/       # Spanner & Graph Services
│   └── main.py         # Application Entrypoint
├── frontend/           # React Frontend
│   ├── src/
│   │   ├── components/ # React Components (Chat, Graph, etc.)
│   │   ├── stores/     # State Management (Zustand)
│   │   └── types/      # TypeScript Definitions
│   └── vite.config.ts  # Vite Configuration
└── spanner-key.json    # GCP Credentials (Do not commit!)
```

## Hybrid Search Test Queries

Use these queries to test if the "Smart Router" is correctly choosing the best search method.

### 🔀 Hybrid Search (The "Smart" Queries)

These should trigger the Hybrid method because they combine specific constraints with natural language.

-   **"Find someone with healing skills in the mountains"**
    -   *Why*: Combines semantic ("healing") + location filter ("mountains").
-   **"Who can build a shelter in the forest?"**
    -   *Why*: Combines semantic ("build a shelter" ≈ construction) + location filter ("forest").
-   **"I need food and water resources near the river"**
    -   *Why*: Multiple concepts + location context.
-   **"Survivors with combat abilities for defense"**
    -   *Why*: "Combat" is a category, "defense" is semantic context.

### 🧬 RAG / Semantic Search (Conceptual)

These should trigger the RAG (Semantic) method because they are vague or ask for similarity.

-   **"Find skills similar to first aid"**
    -   *Why*: Explicit "similar to" trigger.
-   **"Who is good at fixing injuries?"**
    -   *Why*: "Fixing injuries" doesn't match a specific skill name, requires understanding it means "medical/first aid".
-   **"Looking for a leader"**
    -   *Why*: Abstract concept, likely no skill named "leader".
-   **"Who can help with psychological trauma?"**
    -   *Why*: Complex medical concept, likely maps to "comfort" or "counseling" skills.

### 🔤 Keyword Search (Exact Matches)

These should trigger the Keyword method because they are specific and direct.

-   **"List all medical skills"**
    -   *Why*: "Medical" is a likely category name.
-   **"Who is in the forest biome?"**
    -   *Why*: Pure location filter.
-   **"Find survivors with the fishing skill"**
    -   *Why*: "Fishing" is a specific skill name.
-   **"Show me combat specialists"**
    -   *Why*: "Combat" is a category.
