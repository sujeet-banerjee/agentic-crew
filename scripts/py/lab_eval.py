import os
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

# 1. Connect to the local LiteLLM/Ollama proxy via OpenAI SDK
# We use 'dummy' for the key because LiteLLM handles the local routing.
os.environ["OPENAI_API_KEY"] = "dummy-key"

# Point to the LiteLLM container on port 4000
judge_model = ChatOpenAI(
    model="ollama/llama3", # Or whichever model you pulled in Ollama
    base_url="http://localhost:4000" 
)
# For local embeddings (you can use Ollama embeddings here too)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small", base_url="http://localhost:4000")

# 2. Define the Test Dataset
data = {
    'question': ['What is the capital of France?'],
    'answer': ['Paris is the capital.'],
    'contexts' : [['France is a country in Europe. Its capital is Paris.']],
}
dataset = Dataset.from_dict(data)

# 3. Run Ragas Evaluation
print("Evaluating model outputs locally...")
score = evaluate(dataset=dataset, metrics=[faithfulness, answer_relevancy], llm=judge_model, embeddings=embeddings)

print("\n--- Evaluation Results ---")
print(score.to_pandas())