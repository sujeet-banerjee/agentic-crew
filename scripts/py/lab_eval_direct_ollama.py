import os
import pandas as pd
from openai import OpenAI

from ragas import EvaluationDataset, evaluate
from ragas.llms import llm_factory
from ragas.embeddings.base import embedding_factory

# 1. Import Ragas Semantic Metrics AND Traditional Lexical Metrics
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    AnswerCorrectness,  # Compares response against reference semantically
    BleuScore,  # Traditional Lexical Metric (n-gram precision)
    RougeScore  # Traditional Lexical Metric (longest common subsequence)
)

os.environ["OPENAI_API_KEY"] = "dummy-key"

# 2. Initialize local Ollama client
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="dummy-key"
)

# Create Ragas wrappers
ragas_llm = llm_factory(model="llama3", client=ollama_client)
ragas_emb = embedding_factory(provider="openai", model="nomic-embed-text", client=ollama_client)

# 3. Define the Comparative Dataset
dataset = EvaluationDataset.from_list([
    {
        # Case 1: Lexical Match (Exact words used - BLEU & RAGAS will both score well)
        "user_input": "What is the capital of France?",
        "response": "Paris is the capital of France.",
        "retrieved_contexts": ["France is a country in Europe. Its capital is Paris."],
        "reference": "Paris is the capital of France."
    },
    {
        # Case 2: Semantic Match, Lexical Mismatch (BLEU will fail, RAGAS will pass)
        "user_input": "What is the company vacation policy?",
        "response": "Workers are given 15 days of paid leave per year.",
        "retrieved_contexts": ["Employees get 15 days of paid time off annually. Sick leave is separate."],
        "reference": "Employees get 15 days of paid time off annually."
    }
])

# 4. Initialize all metrics
metrics = [
    # --- LLM-as-a-Judge Metrics (Understands Meaning) ---
    Faithfulness(llm=ragas_llm),
    AnswerRelevancy(llm=ragas_llm, embeddings=ragas_emb),
    ContextPrecision(llm=ragas_llm),
    ContextRecall(llm=ragas_llm),
    AnswerCorrectness(llm=ragas_llm, embeddings=ragas_emb),

    # --- Traditional NLP Metrics (Only understands exact word overlap) ---
    BleuScore(),
    RougeScore()
]

# 5. Execute Evaluation
print("Evaluating model outputs directly via Ollama (This may take a minute)...")
results = evaluate(
    dataset=dataset,
    metrics=metrics
)

# 6. Display Results in a Table
print("\n--- Full Evaluation Results ---")
df = results.to_pandas()

# Filter to show just the columns that highlight the BLEU vs RAGAS battle
comparison_df = df[[
    'user_input',
    'response',
    'faithfulness',
    'answer_correctness',
    'bleu_score',
    'rouge_score'
]]

print("\n" + comparison_df.to_string(index=False))