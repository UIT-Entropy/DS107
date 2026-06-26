from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pathlib import Path
import pandas as pd

from advisor.core.advisor import RicePestAdvisor


BENCHMARK_FILE = "benchmark_questions.csv"
OUTPUT_FILE = "retrieval_results.csv"

TOP_K = 5
CANDIDATE_K = 20


def build_retrieval_query(question: str, class_id: str) -> str:
    """
    Mô phỏng đúng flow production:

    YOLO -> class_id
         -> retrieval question
         -> retrieve()
    """
    return f"Benh/sau da biet tu YOLO: {class_id}. {question}"


def main():

    advisor = RicePestAdvisor()

    questions_df = pd.read_csv(BENCHMARK_FILE)

    all_rows = []

    for _, row in questions_df.iterrows():

        question_id = row["id"]
        class_id = row["class_id"]
        question = row["question"]
        intent = row["intent"]
        expected_section = row["expected_section"]

        retrieval_query = build_retrieval_query(
            question=question,
            class_id=class_id,
        )

        try:

            results = advisor.retrieve(
                retrieval_query,
                top_k=TOP_K,
                candidate_k=CANDIDATE_K,
            )

            for result in results:

                chunk = result.chunk

                retrieved_class = chunk.get("class_id", "")
                retrieved_section = chunk.get("section", "")

                all_rows.append({
                    "question_id": question_id,
                    "question": question,

                    "target_class": class_id,
                    "intent": intent,
                    "expected_section": expected_section,

                    "rank": result.rank,

                    "embedding_score":
                        result.embedding_score,

                    "rerank_score":
                        result.rerank_score,

                    "retrieved_class":
                        retrieved_class,

                    "retrieved_section":
                        retrieved_section,

                    "is_class_match":
                        retrieved_class == class_id,

                    "is_section_match":
                        retrieved_section == expected_section,

                    "chunk_id":
                        chunk.get("chunk_id", ""),

                    "source_org":
                        chunk.get("source_org", ""),

                    "source_url":
                        chunk.get("source_url", ""),

                    "source_tier":
                        chunk.get("source_tier", ""),

                    "source_relation":
                        chunk.get("source_relation", ""),

                    "chunk_text":
                        chunk.get("text", ""),
                })

        except Exception as e:

            all_rows.append({
                "question_id": question_id,
                "question": question,

                "target_class": class_id,
                "intent": intent,
                "expected_section": expected_section,

                "rank": -1,
                "embedding_score": None,
                "rerank_score": None,

                "retrieved_class": "",
                "retrieved_section": "",

                "is_class_match": False,
                "is_section_match": False,

                "chunk_id": "",
                "source_org": "",
                "source_url": "",
                "source_tier": "",
                "source_relation": "",

                "chunk_text": "",

                "error": str(e),
            })

            print(
                f"[ERROR] Question {question_id}: {e}"
            )

    results_df = pd.DataFrame(all_rows)

    results_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"Saved {len(results_df)} rows "
        f"to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()