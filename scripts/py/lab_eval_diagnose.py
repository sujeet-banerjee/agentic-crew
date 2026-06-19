import os
from datasets import Dataset
# Updated Ragas imports
from ragas.metrics.collections import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    FactualCorrectness,
    ResponseGroundedness,
    AnswerAccuracy
)

from ragas import evaluate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

import ragas
print("Ragas:", ragas.__version__)

from ragas.metrics.collections import faithfulness
print(type(faithfulness))
print(faithfulness)

for x in dir(faithfulness):
    if not x.startswith("_"):
        print(x)


from ragas.metrics.collections import (
    faithfulness,
    answer_relevancy,
    answer_accuracy,
    context_precision,
    context_recall,
    factual_correctness,
    response_groundedness,
)

mods = [
    faithfulness,
    answer_relevancy,
    answer_accuracy,
    context_precision,
    context_recall,
    factual_correctness,
    response_groundedness,
]

for mod in mods:
    print("\nMODULE:", mod.__name__)
    for name in dir(mod):
        if not name.startswith("_"):
            print(" ", name)

from ragas.metrics.collections.faithfulness import Faithfulness

m = Faithfulness()
print(m)