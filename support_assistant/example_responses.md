# Verified mock-mode HTTP calls

Server: `python -m uvicorn support_assistant.main:app --host 127.0.0.1 --port 7860`; `MOCK_LLM` unset.

## `POST /ask` — What is the delivery fee?

```json
{"answer":"Based on the retrieved context: Zepto delivers grocery and household essentials to serviceable pin codes within 10 to 30 minutes of order confirmation, depending on the customer's delivery zone and current order volume. Standard delivery is free on orders over INR 149; orders below this threshold incur a flat INR 25 delivery fee.","sources":["doc_01","doc_05","doc_02"],"confidence":1.0}
```

## `POST /ask` — What is the capital of France?

```json
{"answer":"I can only answer questions about Zepto policies right now.","sources":[],"confidence":1.0}
```
