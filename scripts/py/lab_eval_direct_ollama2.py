import os
from openai import OpenAI

from ragas import EvaluationDataset, evaluate
from ragas.llms import llm_factory

# 1. FIX: Import the embedding_factory from its new '.base' location to clear the warning
from ragas.embeddings.base import embedding_factory

# 2. THE CRITICAL FIX: Import directly from ragas.metrics (DO NOT use .collections)
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall
)

os.environ["OPENAI_API_KEY"] = "dummy-key"

# Initialize local Ollama client
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="dummy-key"
)

# Create Ragas wrappers
ragas_llm = llm_factory(model="llama3", client=ollama_client)
ragas_emb = embedding_factory(provider="openai", model="nomic-embed-text", client=ollama_client)

# Define dataset using modern EvaluationDataset schema
dataset = EvaluationDataset.from_list([
    {
        "user_input": "What is the capital of France?",
        "response": "Paris is the capital.",
        "retrieved_contexts": ["France is a country in Europe. Its capital is Paris."],
        "reference": "Paris"
    }
])

# 3. Initialize metrics (These now use the base class that evaluate() accepts)
metrics = [
    Faithfulness(llm=ragas_llm),
    AnswerRelevancy(llm=ragas_llm, embeddings=ragas_emb),
    ContextPrecision(llm=ragas_llm),
    ContextRecall(llm=ragas_llm)
]

print("Evaluating model outputs directly via Ollama...")

# Run evaluation
score = evaluate(
    dataset=dataset,
    metrics=metrics
)

print("\n--- Evaluation Results ---")
print(score)