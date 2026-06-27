from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pathlib import Path
import pandas as pd

from advisor_no_rag import RicePestAdvisorNoRAG

INPUT_FILE = "benchmark_questions.csv"
OUTPUT_FILE = "no_rag_answers.csv"


def main():

    advisor = RicePestAdvisorNoRAG()

    df = pd.read_csv(INPUT_FILE)

    rows = []

    for _, row in df.iterrows():

        result = advisor.answer(
            question=row["question"],
            class_id=row["class_id"],
        )

        rows.append({
            "question_id": row["id"],
            "class_id": row["class_id"],
            "question": row["question"],
            "answer": result.text,
        })

        print(row["id"])

    pd.DataFrame(rows).to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
