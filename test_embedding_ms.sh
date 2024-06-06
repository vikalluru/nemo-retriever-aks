curl -X POST "http://localhost:8000/v1/embeddings" \
-H "accept: application/json" \
-H "Content-Type: application/json" \
-d '{"input": ["Hello"], "model": "NV-Embed-QA", "input_type": "query"}'