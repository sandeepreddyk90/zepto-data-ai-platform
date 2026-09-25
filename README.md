# Zepto Data & AI Platform

One Python repository with three connected engineering workflows. The catalogue pipeline stores structured pricing data; the analytics pipeline profiles and models a customer-style dataset; the support assistant retrieves Zepto policy text. These are distinct data sources sharing one reproducible project layout.

## Setup

Python 3.11 or 3.12 is recommended. Each module has its own `requirements.txt`; install all three for the complete project:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -r data_pipeline/requirements.txt -r analytics/requirements.txt -r support_assistant/requirements.txt
```

## Run in order

```bash
python data_pipeline/pipeline.py
python analytics/01_eda.py
python analytics/02_modeling.py
python -m uvicorn support_assistant.main:app --host 127.0.0.1 --port 7860
```

The analytics first step initially calls `sns.load_dataset('titanic')` and writes `analytics/titanic.csv`; subsequent runs read the committed CSV unless `--refresh` is supplied. The modeling script only reads that CSV. The assistant defaults to offline deterministic generation (`MOCK_LLM` unset or `1`); the embedding model must be downloaded once before offline use. See each module README for methods, results, and limitations.

## Design decisions

- **Catalogue:** scrape three chosen categories with pagination, clean defensively, and persist normalized `categories` and `books` tables. INR conversion uses the assignment's fixed **1 GBP = 105.50 INR** baseline; it is not a market quote.
- **Analytics:** retain one raw Titanic CSV for an offline fallback; write a separately derived clean CSV for EDA and modeling. All learned preprocessing is inside train-fitted pipelines. Feature choices exclude fields that directly encode the target.
- **Assistant:** preserve each policy as a source-identifiable chunk, index local embeddings in Chroma, and route questions through LangGraph. Only generation/classification may use an optional remote model; retrieval always runs locally.

## Git workflow

The included Git history has two commits on `feature/platform` merged into `main`. Inspect it with `git log --graph --all --oneline`. Publish **this one repository** to a public GitHub repository and submit only its URL. Review and adapt the code and written interpretations as your own work before an academic submission.
## Running in Google Colab

After opening the project folder in Colab, install the module requirements and run the scripts in order:

```python
!pip install -r data_pipeline/requirements.txt -r analytics/requirements.txt -r support_assistant/requirements.txt
!python data_pipeline/pipeline.py
!python analytics/01_eda.py
!python analytics/02_modeling.py
```

The support assistant uses deterministic mock mode by default and requires no LLM API key.
