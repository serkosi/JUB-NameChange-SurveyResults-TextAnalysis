#!/usr/bin/env python3
"""Recreate the survey's charts and word clouds with local Python packages."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from wordcloud import STOPWORDS, WordCloud


WORKBOOK_NAME = (
    "collected_data_20221101_JUB Survey on Renaming (Responses) - Anonymised.xlsx"
)

COLUMNS = {
    "status": "What is your current status at the University? ",
    "field": "What is your field of study/research/work? ",
    "heard": "Have you heard about the renaming plans of Jacobs University Bremen? ",
    "meeting": "Have you attended the Town Hall meeting on September 22nd? ",
    "remain": (
        "Do you want the current name of the University - Jacobs University "
        "Bremen - to remain? "
    ),
    "association": (
        "How strongly do you feel your association with "
        "“Jacobs University Bremen”?"
    ),
    "jub_associations": (
        "What comes to your mind when you hear the name of the University - "
        "“Jacobs University Bremen”?\n"
        "(Please write several words or phrases which first come to your mind)"
    ),
    "constructor_associations": (
        "What comes to your mind when you hear the name of the University - "
        "“Constructor University”?\n"
        "(Please write several words or phrases which first come to your mind)"
    ),
    "constructor_feeling": (
        'How do you feel about renaming the University as "Constructor University"?'
    ),
    "constructor_intent": (
        'Do you want to study/work at the "Constructor University"? '
    ),
    "alternative_name": (
        "In case the current name is not kept, which name do you think Jacobs "
        "University Bremen should have in the future?"
    ),
    "ideas": (
        "Please share your ideas and suggestions with the GSA and BIGSSS Fellow "
        "Representatives."
    ),
}

NAME_PATTERNS = (
    (
        "Bremen Institute of Technology and Science",
        re.compile(
            r"\bbremen\s+institute\s+of\s+technology\s+and\s+science\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Bremen Institute of Technology",
        re.compile(
            r"\b(?:bit\s*[-–]\s*bremen\s+institute\s+of\s+tech(?:n|m)ology|"
            r"bremen\s+institute\s+of\s+technology)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "International University Bremen",
        re.compile(
            r"\b(?:international|university|bremen)\b",
            re.IGNORECASE,
        ),
    ),
)

UNIQUE_NAME_EXAMPLES = (
    "I think the most healty thing",
    "So a name should embody the spirit of diversity that jacobs champions",
    "any name which is not clearly associated with a potential",
    "society/politics etc.",
    "none of the above represents what Jacobs stands for",
    "Different unique name",
    "Some artificial name that vaguely sounds like Latin",
)

OTHER_NAME_EXAMPLES = (
    "Polytechnische Hochschule Bremen",
    "Charles Babbage University",
    "Bell University Bremen",
    "Jacobs International University",
    "Jacobs University is in itself a best name this university can have",
    "Technique University Bremen",
    "Bremen Technological University",
    "Bremen University of Science and Technology",
    "Slay University",
    "Paradigm University",
    "options besides Constructor",
    "Wesser River University",
    "Lucid Dream University",
    "For Whom The Bell Tolls",
    "except Constructor Univeristy",
    "Schaffhausen Institute of Technology Bremen",
    "?",
    "Bell University",
    "Bell International University",
    "Innovator",
    "Constructive",
    "International Global Challenges University (IGCU)",
    "None of Them",
)

WORD_CLOUD_STOPWORDS = STOPWORDS.union(
    {"university", "uni", "jacobs", "constructor", "name"}
)


def load_responses(workbook_path: Path) -> pd.DataFrame:
    """Load the response sheet and verify that it has the expected questions."""
    try:
        responses = pd.read_excel(workbook_path, sheet_name=0, engine="openpyxl")
    except (OSError, ValueError, ImportError) as exc:
        raise ValueError(f"Could not read survey workbook {workbook_path}: {exc}") from exc

    missing = [column for column in COLUMNS.values() if column not in responses.columns]
    if missing:
        raise ValueError(
            "The survey workbook is missing expected columns: "
            + ", ".join(repr(column) for column in missing)
        )
    return responses


def valid_text(values: Iterable[object]) -> list[str]:
    """Return non-empty response strings."""
    return [
        str(value).strip()
        for value in values
        if pd.notna(value) and str(value).strip()
    ]


def recode_status(value: str) -> str:
    other_terms = (
        "parents",
        "retired",
        "(non-)",
        "postdoc",
        "foundation",
        "adjunct",
        "freelancer",
        "exchange",
        "/faculty",
    )
    if any(term in value.casefold() for term in other_terms):
        return "Other Response Options"
    return value


def recode_alternative_name(value: str) -> str:
    folded = value.casefold()
    if "iub" in folded or all(
        term in folded for term in ("international", "university", "bremen")
    ):
        return "International University Bremen"
    for label, pattern in NAME_PATTERNS[:2]:
        if pattern.search(value):
            return label
    if any(example.casefold() in folded for example in UNIQUE_NAME_EXAMPLES):
        return "A Unique Name"
    if any(example.casefold() in folded for example in OTHER_NAME_EXAMPLES):
        return "Other Response Options"
    return value


def normalized_text(series: pd.Series) -> list[str]:
    return valid_text(series.tolist())


def word_frequencies(text: str) -> Counter[str]:
    cleaned = re.sub(
        r"\b(?:university|uni|jacobs|constructor|name)\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    words = re.findall(r"[^\W\d_]+(?:['’-][^\W\d_]+)*", cleaned, flags=re.UNICODE)
    return Counter(
        word.casefold()
        for word in words
        if len(word) > 1 and word.casefold() not in WORD_CLOUD_STOPWORDS
    )


def write_chart(figure: plt.Figure, output_directory: Path, stem: str) -> None:
    for extension in ("png", "svg"):
        figure.savefig(
            output_directory / f"{stem}.{extension}",
            bbox_inches="tight",
            dpi=180,
        )
    plt.close(figure)


def plot_categorical(
    series: pd.Series,
    title: str,
    stem: str,
    output_directory: Path,
    *,
    limit: int | None = None,
) -> pd.Series:
    values = valid_text(series.tolist())
    counts = pd.Series(Counter(values), dtype="int64").sort_values(
        ascending=False, kind="stable"
    )
    if counts.empty:
        return counts

    shown = counts if limit is None else counts.head(limit)
    if len(shown) <= 6:
        figure, axis = plt.subplots(figsize=(9, 6))
        axis.pie(
            shown.values,
            labels=[f"{label} ({count})" for label, count in shown.items()],
            autopct="%1.1f%%",
            startangle=90,
            textprops={"fontsize": 9},
        )
        axis.axis("equal")
    else:
        figure, axis = plt.subplots(figsize=(10, max(5, len(shown) * 0.32)))
        axis.barh(shown.index.astype(str)[::-1], shown.values[::-1], color="#4169a1")
        axis.set_xlabel("Response count")
        axis.grid(axis="x", alpha=0.25)
        for index, count in enumerate(shown.values[::-1]):
            axis.text(count, index, f" {count}", va="center", fontsize=8)
    axis.set_title(title, fontsize=12, pad=14)
    figure.tight_layout()
    write_chart(figure, output_directory, stem)
    return counts


def plot_score(
    series: pd.Series,
    title: str,
    stem: str,
    output_directory: Path,
) -> pd.Series:
    scores = pd.to_numeric(series, errors="coerce").dropna()
    if scores.empty:
        return pd.Series(dtype="int64")
    if ((scores < 0) | (scores > 10)).any():
        invalid = sorted(scores[(scores < 0) | (scores > 10)].unique().tolist())
        raise ValueError(f"{title} contains scores outside the 0-10 scale: {invalid}")

    counts = scores.astype(int).value_counts().reindex(range(11), fill_value=0)
    figure, axis = plt.subplots(figsize=(9, 5))
    bars = axis.bar(counts.index, counts.values, color="#8b5a2b")
    axis.set_xticks(range(11))
    axis.set_xlabel("Rating (0-10)")
    axis.set_ylabel("Response count")
    axis.grid(axis="y", alpha=0.25)
    total = int(counts.sum())
    for bar, count in zip(bars, counts.values):
        axis.annotate(
            f"{count} ({count / total:.1%})",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            fontsize=7,
        )
    axis.set_title(title, fontsize=12, pad=14)
    figure.tight_layout()
    write_chart(figure, output_directory, stem)
    return counts[counts > 0]


def plot_word_cloud(
    text: str,
    title: str,
    stem: str,
    output_directory: Path,
) -> Counter[str]:
    frequencies = word_frequencies(text)
    if not frequencies:
        print(f"Skipping empty word cloud: {title}", file=sys.stderr)
        return frequencies

    cloud = WordCloud(
        width=1400,
        height=900,
        background_color="white",
        colormap="tab10",
        stopwords=WORD_CLOUD_STOPWORDS,
        collocations=False,
        random_state=17,
    ).generate_from_frequencies(frequencies)
    figure, axis = plt.subplots(figsize=(12, 8))
    axis.imshow(cloud, interpolation="bilinear")
    axis.axis("off")
    axis.set_title(title, fontsize=12, pad=14)
    figure.tight_layout()
    write_chart(figure, output_directory, stem)
    return frequencies


def export_counts(output_directory: Path, counts: dict[str, pd.Series]) -> None:
    rows = []
    for question, series in counts.items():
        total = int(series.sum())
        for answer, count in series.items():
            rows.append(
                {
                    "question": question,
                    "answer": answer,
                    "count": int(count),
                    "percentage": round(100 * int(count) / total, 2) if total else 0,
                }
            )
    pd.DataFrame(rows).to_csv(output_directory / "response_counts.csv", index=False)


def export_word_frequencies(
    output_directory: Path,
    frequencies_by_question: dict[str, Counter[str]],
) -> None:
    rows = [
        {"question": question, "term": term, "frequency": frequency}
        for question, frequencies in frequencies_by_question.items()
        for term, frequency in frequencies.most_common()
    ]
    pd.DataFrame(rows, columns=["question", "term", "frequency"]).to_csv(
        output_directory / "word_frequencies.csv",
        index=False,
    )


def analyze(workbook_path: Path, output_directory: Path) -> tuple[int, int]:
    responses = load_responses(workbook_path)
    output_directory.mkdir(parents=True, exist_ok=True)
    counts: dict[str, pd.Series] = {}

    status = responses[COLUMNS["status"]].map(
        lambda value: recode_status(str(value).strip()) if pd.notna(value) else value
    )
    counts["Q1 Current status"] = plot_categorical(
        status, "Q1 - Current status at the University", "q01_status", output_directory
    )
    counts["Q2 Field of study/research/work"] = plot_categorical(
        responses[COLUMNS["field"]],
        "Q2 - Field of study, research, or work (top 20)",
        "q02_field",
        output_directory,
        limit=20,
    )
    counts["Q3 Heard about renaming plans"] = plot_categorical(
        responses[COLUMNS["heard"]],
        "Q3 - Heard about the renaming plans",
        "q03_heard_about_plans",
        output_directory,
    )
    counts["Q4 Attended Town Hall"] = plot_categorical(
        responses[COLUMNS["meeting"]],
        "Q4 - Attended the Town Hall meeting",
        "q04_town_hall",
        output_directory,
    )
    counts["Q5 Keep current name"] = plot_categorical(
        responses[COLUMNS["remain"]],
        "Q5 - Keep the current University name",
        "q05_keep_current_name",
        output_directory,
    )
    counts["Q6 Association with current name"] = plot_score(
        responses[COLUMNS["association"]],
        "Q6 - Association with Jacobs University Bremen",
        "q06_association",
        output_directory,
    )

    word_frequencies_by_question: dict[str, Counter[str]] = {}
    for key, title, stem in (
        (
            "jub_associations",
            "Q7 - Associations with Jacobs University Bremen",
            "q07_jub_wordcloud",
        ),
        (
            "constructor_associations",
            "Q8 - Associations with Constructor University",
            "q08_constructor_wordcloud",
        ),
        (
            "ideas",
            "Q12 - Suggestions and ideas",
            "q12_ideas_wordcloud",
        ),
    ):
        text = " ".join(normalized_text(responses[COLUMNS[key]]))
        word_frequencies_by_question[title] = plot_word_cloud(
            text, title, stem, output_directory
        )

    counts["Q9 Feeling about Constructor University"] = plot_score(
        responses[COLUMNS["constructor_feeling"]],
        "Q9 - Feeling about renaming to Constructor University",
        "q09_constructor_feeling",
        output_directory,
    )
    counts["Q10 Study/work at Constructor University"] = plot_categorical(
        responses[COLUMNS["constructor_intent"]],
        "Q10 - Study or work at Constructor University",
        "q10_constructor_intent",
        output_directory,
    )
    alternative_names = responses[COLUMNS["alternative_name"]].map(
        lambda value: (
            recode_alternative_name(str(value).strip()) if pd.notna(value) else value
        )
    )
    counts["Q11 Alternative name"] = plot_categorical(
        alternative_names,
        "Q11 - Suggested future name (top 20)",
        "q11_alternative_names",
        output_directory,
        limit=20,
    )

    export_counts(output_directory, counts)
    export_word_frequencies(output_directory, word_frequencies_by_question)
    return len(responses), sum(len(series) for series in counts.values())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create survey charts and word clouds from the anonymized workbook."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).resolve().parent / WORKBOOK_NAME,
        help="Path to the survey workbook (defaults to the workbook in this repository).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "analysis_graphics",
        help="Directory for PNG/SVG charts and CSV summaries.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        response_count, summarized_categories = analyze(args.input, args.output_dir)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"Analyzed {response_count} survey responses. "
        f"Created 12 charts (PNG and SVG) and 2 CSV summaries in "
        f"{args.output_dir.resolve()}."
    )
    print(f"Summarized {summarized_categories} response categories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
