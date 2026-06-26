from pathlib import Path
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent

INPUT_FILE = SCRIPT_DIR / "retrieval_results.csv"
OUTPUT_FILE = SCRIPT_DIR / "retrieval_metrics.csv"

SECTION_ALIASES = {
    "ipm_management": "management_ipm",
}


def normalize_section(section):
    section = str(section)
    return SECTION_ALIASES.get(section, section)


def compute_metrics(df):

    question_ids = sorted(df["question_id"].unique())

    class_hits = 0
    section_hits = 0

    reciprocal_ranks = []

    for qid in question_ids:

        qdf = (
            df[df["question_id"] == qid]
            .sort_values("rank")
        )

        target_class = qdf.iloc[0]["target_class"]
        expected_section = normalize_section(qdf.iloc[0]["expected_section"])

        class_match = (
            qdf["retrieved_class"]
            == target_class
        )

        section_match = qdf["retrieved_section"].map(normalize_section) == expected_section

        if class_match.any():
            class_hits += 1

        if section_match.any():
            section_hits += 1

        rr = 0.0

        for _, row in qdf.iterrows():

            if row["retrieved_class"] == target_class:
                rr = 1.0 / row["rank"]
                break

        reciprocal_ranks.append(rr)

    total_questions = len(question_ids)

    metrics = {
        "num_questions": total_questions,
        "class_hit_at_5": class_hits / total_questions,
        "section_hit_at_5": section_hits / total_questions,
        "mrr_at_5": sum(reciprocal_ranks) / total_questions,
    }

    return metrics


def main():

    df = pd.read_csv(INPUT_FILE)

    metrics = compute_metrics(df)

    metrics_df = pd.DataFrame([metrics])

    metrics_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print(metrics_df)

    print(
        f"Saved metrics to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
