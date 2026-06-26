import pandas as pd
import numpy as np

from rouge_score import rouge_scorer
from bert_score import score
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


REFERENCE_FILE = "reference_answer.csv"
RAG_FILE = "answer_rag_results.csv"
NO_RAG_FILE = "no_rag_answers.csv"


reference = pd.read_csv(REFERENCE_FILE)

rag = pd.read_csv(RAG_FILE)

norag = pd.read_csv(NO_RAG_FILE)

reference_map = dict(
    zip(
        reference["id"],
        reference["reference_answer"]
    )
)

model = SentenceTransformer(
    "paraphrase-multilingual-MiniLM-L12-v2"
)


def evaluate(predictions, references):

    scorer = rouge_scorer.RougeScorer(
        ["rougeL"],
        use_stemmer=True
    )

    rouge_scores = []

    for ref, pred in zip(references, predictions):

        score_result = scorer.score(
            str(ref),
            str(pred)
        )

        rouge_scores.append(
            score_result["rougeL"].fmeasure
        )

    rouge_l = np.mean(rouge_scores)

    _, _, f1 = score(
        predictions,
        references,
        lang="vi"
    )

    bertscore = float(f1.mean())

    ref_embeddings = model.encode(
        references,
        convert_to_numpy=True
    )

    pred_embeddings = model.encode(
        predictions,
        convert_to_numpy=True
    )

    similarities = []

    for ref_emb, pred_emb in zip(
        ref_embeddings,
        pred_embeddings
    ):

        sim = cosine_similarity(
            [ref_emb],
            [pred_emb]
        )[0][0]

        similarities.append(sim)

    semantic_similarity = np.mean(similarities)

    return {
        "ROUGE_L": rouge_l,
        "BERTScore": bertscore,
        "SemanticSimilarity": semantic_similarity
    }


rag_refs = [
    reference_map[qid]
    for qid in rag["question_id"]
]

rag_preds = (
    rag["generated_answer"]
    .fillna("")
    .astype(str)
    .tolist()
)

rag_metrics = evaluate(
    rag_preds,
    rag_refs
)


norag_refs = [
    reference_map[qid]
    for qid in norag["question_id"]
]

norag_preds = (
    norag["answer"]
    .fillna("")
    .astype(str)
    .tolist()
)

norag_metrics = evaluate(
    norag_preds,
    norag_refs
)

result = pd.DataFrame([
    {
        "System": "No-RAG",
        **norag_metrics
    },
    {
        "System": "RAG",
        **rag_metrics
    }
])

result.to_csv(
    "generation_metrics.csv",
    index=False
)

print(result)