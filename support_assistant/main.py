"""Local embeddings/Chroma + LangGraph intent routing + validated FastAPI output."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

import chromadb
import requests
from fastapi import FastAPI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

from .prompt import GROUNDED_PROMPT

ROOT = Path(__file__).resolve().parent
KEYWORDS = ("delivery", "return", "refund", "membership", "tracking", "cancel", "gift card", "support hours")


class AskRequest(BaseModel):
    query: str = Field(min_length=1)


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float = Field(ge=0, le=1)


class AssistantState(TypedDict, total=False):
    query: str
    intent: str
    response: AskResponse


def mock_mode() -> bool:
    return os.getenv("MOCK_LLM", "1") != "0"


@lru_cache(maxsize=1)
def index():
    """One short chunk per exact corpus document; idempotent Chroma upsert."""
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=str(ROOT / "chroma_store"))
    collection = client.get_or_create_collection("zepto_policies", metadata={"hnsw:space": "cosine"})
    paths = sorted((ROOT / "docs").glob("doc_*.txt"))
    if len(paths) != 8:
        raise RuntimeError("Expected eight policy files")
    docs = [p.read_text(encoding="utf-8").strip() for p in paths]
    ids = [p.stem for p in paths]
    vectors = model.encode(docs, normalize_embeddings=True).tolist()
    collection.upsert(ids=ids, documents=docs, embeddings=vectors, metadatas=[{"filename": p.name} for p in paths])
    return model, collection


def real_llm(prompt: str) -> str:
    """Optional Groq free-tier path; never reached unless MOCK_LLM=0."""
    key = os.environ["GROQ_API_KEY"]
    resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"), "messages": [{"role": "user", "content": prompt}], "temperature": 0}, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def checked_real(prompt: str, allowed_sources: list[str]) -> AskResponse:
    """Initial call plus at most two corrective retries on invalid model output."""
    for attempt in range(3):
        raw = real_llm(prompt)
        try:
            result = AskResponse.model_validate_json(raw)
            if any(source not in allowed_sources for source in result.sources):
                raise ValueError("source not among retrieved chunks")
            return result
        except (ValueError, json.JSONDecodeError) as exc:
            prompt += f"\nCorrection {attempt + 1}: Return valid JSON with answer, sources drawn ONLY from {allowed_sources}, and confidence in [0,1]. Previous error: {exc}."
    return AskResponse(answer="ERROR: real LLM output failed schema validation after 3 attempts.", sources=[], confidence=0.0)


def classify_intent(state: AssistantState) -> AssistantState:
    if mock_mode():
        intent = "policy_question" if any(word in state["query"].lower() for word in KEYWORDS) else "general_question"
    else:
        raw = real_llm("Classify as exactly policy_question or general_question: " + state["query"])
        intent = "policy_question" if "policy_question" in raw else "general_question"
    return {"intent": intent}


def route(state: AssistantState) -> str:
    return "retrieve_and_answer" if state["intent"] == "policy_question" else "direct_answer"


def retrieve_and_answer(state: AssistantState) -> AssistantState:
    model, collection = index()
    vec = model.encode([state["query"]], normalize_embeddings=True).tolist()
    matches = collection.query(query_embeddings=vec, n_results=3, include=["documents", "distances"])
    ids, docs = matches["ids"][0], matches["documents"][0]
    if mock_mode():
        snippet = ". ".join(docs[0].split(". ")[:2]).rstrip(".") + "."
        response = AskResponse(answer=f"Based on the retrieved context: {snippet}", sources=ids, confidence=1.0)
    else:
        context = "\n".join(f"[{i}] {d}" for i, d in zip(ids, docs))
        response = checked_real(GROUNDED_PROMPT.format(context=context, query=state["query"]), ids)
    return {"response": response}


def direct_answer(state: AssistantState) -> AssistantState:
    if mock_mode():
        response = AskResponse(answer="I can only answer questions about Zepto policies right now.", sources=[], confidence=1.0)
    else:
        response = checked_real("Answer this general question briefly as JSON with answer, sources=[], confidence (0..1): " + state["query"], [])
    return {"response": response}


builder = StateGraph(AssistantState)
builder.add_node("classify_intent", classify_intent)
builder.add_node("retrieve_and_answer", retrieve_and_answer)
builder.add_node("direct_answer", direct_answer)
builder.add_edge(START, "classify_intent")
builder.add_conditional_edges("classify_intent", route, {"retrieve_and_answer": "retrieve_and_answer", "direct_answer": "direct_answer"})
builder.add_edge("retrieve_and_answer", END)
builder.add_edge("direct_answer", END)
graph = builder.compile()
app = FastAPI(title="Zepto Policy Assistant")


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    return AskResponse.model_validate(graph.invoke({"query": request.query})["response"])
