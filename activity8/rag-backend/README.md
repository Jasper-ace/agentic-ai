# Lumina RAG Chat Backend

A Retrieval-Augmented Generation (RAG) backend utilizing Python/Flask, Gemini (Embedding & Generation) APIs, and Qdrant Vector Database, running entirely within Docker containers.

---

## Getting Started

### Prerequisites

1. **Docker Desktop**:
   - Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/) for your operating system.
   - Ensure Docker is running.
2. **Gemini API Key**:
   - Obtain an API key from Google AI Studio.

### Configuration

1. Locate the `.env` file in the root of the `rag-backend/` directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here

   QDRANT_HOST=qdrant
   QDRANT_PORT=6333
   QDRANT_COLLECTION=documents

   SIMILARITY_THRESHOLD=0.60
   CHUNK_SIZE=500
   CHUNK_OVERLAP=100
   ```
2. Replace `your_gemini_api_key_here` with your actual Gemini API Key.

### Running the Project

Run the following command from the `rag-backend/` directory to build and start both the backend server and the Qdrant database:

```bash
docker compose up --build
```

- The Flask Backend will be running at `http://localhost:5000`
- The Qdrant Database Dashboard will be running at `http://localhost:6333/dashboard`

---

## API Documentation

### 1. Health Check
Checks the status of the backend API.
- **URL**: `/health`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "status": "ok"
  }
  ```

### 2. Upload Documents
Indexes one or multiple text files. Splits text, generates embeddings with `text-embedding-004`, and upserts to Qdrant.
- **URL**: `/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Body Parameters**:
  - `files`: File object(s) (supports multiple `.txt` files)
- **Response**:
  ```json
  {
    "success": true,
    "files_uploaded": 2,
    "chunks_created": 48
  }
  ```

### 3. Chat
Answers questions using only indexed chunks that meet the 60% similarity threshold.
- **URL**: `/chat`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "message": "What is the policy on annual leave?"
  }
  ```
- **Response**:
  ```json
  {
    "response": "The annual leave policy allows for 20 days of paid time off per calendar year..."
  }
  ```
  *(Note: If no context matches at >= 60% similarity, returns exactly `"I don't know."`)*

### 4. Admin Options

#### List Documents
Returns all files indexed in the vector database.
- **URL**: `/documents`
- **Method**: `GET`

#### Delete Specific Document
Deletes all vectors belonging to a specific file.
- **URL**: `/documents/<filename>`
- **Method**: `DELETE`

#### Delete All Documents
Clears all points and collections.
- **URL**: `/documents`
- **Method**: `DELETE`

---

## Troubleshooting

### 1. "I don't know." Responses
- **Cause**: The similarity score of retrieved chunks is below the `SIMILARITY_THRESHOLD` (default `0.60`).
- **Fix**: Check if you have uploaded the relevant `.txt` files containing the answers. Alternatively, lower the `SIMILARITY_THRESHOLD` in `.env` to test match sensitivity.

### 2. Connection Refused / Backend Offline
- **Cause**: Containers have not started or there is a port conflict.
- **Fix**: Ensure port `5000` and `6333` are free. Run `docker compose ps` to verify that both `rag-backend` and `qdrant-db` container status is `Up`.

### 3. Gemini API Errors
- **Cause**: Missing or invalid `GEMINI_API_KEY`.
- **Fix**: Verify your API key is correctly written in `.env` with no extra spaces or quotation marks, then rebuild using `docker compose down && docker compose up --build`.
