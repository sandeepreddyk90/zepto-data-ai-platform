FROM python:3.11-slim
WORKDIR /app
COPY support_assistant/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY support_assistant /app/support_assistant
ENV MOCK_LLM=1 PYTHONPATH=/app HF_HOME=/app/.cache/huggingface
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
EXPOSE 7860
CMD ["uvicorn", "support_assistant.main:app", "--host", "0.0.0.0", "--port", "7860"]
