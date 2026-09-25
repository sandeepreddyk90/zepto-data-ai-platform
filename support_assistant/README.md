# Zepto policy assistant

## Architecture

**Ingestion:** `main.index()` reads the eight exact policy texts in `docs/`, with one source-labelled chunk per file. **Embedding:** the local `all-MiniLM-L6-v2` SentenceTransformer embeds all eight chunks and `index()` upserts them into ChromaDB's cosine-similarity `zepto_policies` collection (persisted in `chroma_store/`, generated at first use). The model weights must be downloaded once before running offline. **Retrieval:** LangGraph's `classify_intent` routes policy keywords to `retrieve_and_answer`, which embeds the query and requests the top three matches. **Generation:** in the default `MOCK_LLM=1` state, `retrieve_and_answer` copies the top snippet into a deterministic answer, and `direct_answer` returns a fixed sentence for unrelated queries. Only intent classification and generation branch when `MOCK_LLM=0`; retrieval and indexing remain local and real. The optional Groq path requires `GROQ_API_KEY`, uses the structured template in `prompt.py`, and retries malformed response JSON twice. Default mode needs no API key or paid service.

## Local service

From the repository root, after installing `support_assistant/requirements.txt`:

```bash
python -m uvicorn support_assistant.main:app --host 127.0.0.1 --port 7860
curl -s -X POST http://127.0.0.1:7860/ask -H 'Content-Type: application/json' -d '{"query":"What is the delivery fee?"}'
curl -s -X POST http://127.0.0.1:7860/ask -H 'Content-Type: application/json' -d '{"query":"What is the capital of France?"}'
```

## Docker

Build from the repository root (first build downloads the free embedding model):

```bash
docker build -f support_assistant/Dockerfile -t zepto-assistant .
docker run --rm -p 7860:7860 zepto-assistant
```

The Docker image pre-downloads model weights at build time; its default `/ask` path needs no LLM network connection. Example raw JSON responses from a verified default-mode local run are recorded in `example_responses.md`.
