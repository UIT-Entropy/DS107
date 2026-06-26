from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from advisor.core.advisor import RicePestAdvisor


BENCHMARK_FILE = "benchmark_questions.csv"
OUTPUT_FILE = "answer_rag_results.csv"


def main():

    advisor = RicePestAdvisor()

    questions_df = pd.read_csv(BENCHMARK_FILE)

    rows = []

    for _, row in questions_df.iterrows():

        question_id = row["id"]
        question = row["question"]
        class_id = row["class_id"]

        try:

            answer = advisor.answer(
                question=question,
                session_id=None,
            )

            rows.append({
                "question_id": question_id,
                "class_id": class_id,
                "question": question,
                "generated_answer": answer.text,
            })

            print(
                f"[OK] {question_id}"
            )

        except Exception as e:

            rows.append({
                "question_id": question_id,
                "class_id": class_id,
                "question": question,
                "generated_answer": "",
                "error": str(e),
            })

            print(
                f"[ERROR] {question_id}: {e}"
            )

    pd.DataFrame(rows).to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"Saved to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()