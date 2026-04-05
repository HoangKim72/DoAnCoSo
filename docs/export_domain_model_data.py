from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


EXCEL_MAX_DATA_ROWS = 1_048_575
EXCEL_CELL_MAX_LENGTH = 32_767
ILLEGAL_EXCEL_CHARACTERS = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export domain datasets and domain model outputs to Excel for manual review."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output .xlsx path. Defaults to the Desktop.",
    )
    return parser.parse_args()


def resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

 
def resolve_desktop_dir() -> Path:
    candidates = []

    user_profile = os.environ.get("USERPROFILE", "").strip()
    if user_profile:
        candidates.append(Path(user_profile) / "Desktop")

    one_drive = os.environ.get("OneDrive", "").strip()
    if one_drive:
        candidates.append(Path(one_drive) / "Desktop")

    candidates.append(Path.home() / "Desktop")

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists():
            return candidate

    fallback = Path.home()
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def resolve_output_path(custom_output: Path | None, prefix: str) -> Path:
    if custom_output is not None:
        custom_output.parent.mkdir(parents=True, exist_ok=True)
        return custom_output

    desktop_dir = resolve_desktop_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return desktop_dir / f"{prefix}_{timestamp}.xlsx"


def sanitize_excel_value(value: object) -> object:
    if isinstance(value, str):
        cleaned = ILLEGAL_EXCEL_CHARACTERS.sub("", value)
        if len(cleaned) > EXCEL_CELL_MAX_LENGTH:
            return cleaned[:EXCEL_CELL_MAX_LENGTH]
        return cleaned
    return value


def sanitize_dataframe_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    target_columns = cleaned.select_dtypes(include=["object", "string"]).columns
    for column in target_columns:
        cleaned[column] = cleaned[column].map(sanitize_excel_value)
    return cleaned


def truncate_for_excel(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    truncated = len(df) > EXCEL_MAX_DATA_ROWS
    export_df = df.iloc[:EXCEL_MAX_DATA_ROWS].copy() if truncated else df.copy()
    return sanitize_dataframe_for_excel(export_df), truncated


def format_sheet(worksheet) -> None:
    worksheet.freeze_panes = "A2"
    if worksheet.max_row > 1 and worksheet.max_column > 0:
        worksheet.auto_filter.ref = worksheet.dimensions


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def build_dataset_overview(frames: list[tuple[str, Path, pd.DataFrame]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for dataset_name, source_path, df in frames:
        label_counts = df["label"].value_counts().to_dict() if "label" in df.columns else {}
        dates = sorted(df["collected_at"].astype(str).unique().tolist()) if "collected_at" in df.columns else []
        rows.append(
            {
                "dataset_name": dataset_name,
                "source_path": str(source_path),
                "rows": int(len(df)),
                "columns": int(len(df.columns)),
                "phishing_rows": int(label_counts.get(1, 0)),
                "benign_rows": int(label_counts.get(0, 0)),
                "phishing_ratio": safe_ratio(int(label_counts.get(1, 0)), int(len(df))),
                "unique_sources": int(df["source"].nunique()) if "source" in df.columns else 0,
                "unique_dates": len(dates),
                "min_date": dates[0] if dates else "",
                "max_date": dates[-1] if dates else "",
            }
        )
    return pd.DataFrame(rows)


def build_label_distribution(df: pd.DataFrame, group_column: str, sort_desc: bool) -> pd.DataFrame:
    if group_column not in df.columns or "label" not in df.columns:
        return pd.DataFrame()

    grouped = df.groupby([group_column, "label"]).size().unstack(fill_value=0)
    grouped = grouped.rename(columns={0: "benign_count", 1: "phishing_count"})
    for column in ["benign_count", "phishing_count"]:
        if column not in grouped.columns:
            grouped[column] = 0

    grouped["total_rows"] = grouped["benign_count"] + grouped["phishing_count"]
    grouped["phishing_ratio"] = grouped["phishing_count"] / grouped["total_rows"].replace(0, 1)
    result = grouped.reset_index()
    if sort_desc:
        result = result.sort_values(["total_rows", group_column], ascending=[False, True]).reset_index(drop=True)
    else:
        result = result.sort_values(group_column).reset_index(drop=True)
    return result


def build_column_profile(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    total_rows = int(len(df))
    for column in df.columns:
        series = df[column]
        null_count = int(series.isna().sum())
        rows.append(
            {
                "column_name": column,
                "dtype": str(series.dtype),
                "null_count": null_count,
                "non_null_count": total_rows - null_count,
                "null_ratio": safe_ratio(null_count, total_rows),
                "unique_non_null_values": int(series.nunique(dropna=True)),
            }
        )
    return pd.DataFrame(rows)


def build_run_summary_frames(models_dir: Path, prefix: str) -> list[tuple[str, pd.DataFrame]]:
    frames: list[tuple[str, pd.DataFrame]] = []

    run_summary_path = models_dir / "run_summary.json"
    if run_summary_path.exists():
        payload = json.loads(run_summary_path.read_text(encoding="utf-8"))
        overview = {}
        for key, value in payload.items():
            overview[key] = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
        frames.append((f"{prefix}_run_summary", pd.DataFrame([overview])))

    csv_mappings = [
        ("validation_metrics.csv", f"{prefix}_validation_metrics"),
        ("test_metrics.csv", f"{prefix}_test_metrics"),
        ("model_comparison.csv", f"{prefix}_model_comparison"),
    ]
    for filename, sheet_name in csv_mappings:
        path = models_dir / filename
        if path.exists():
            frames.append((sheet_name, pd.read_csv(path)))

    return frames


def write_sheet(
    writer: pd.ExcelWriter,
    sheet_name: str,
    df: pd.DataFrame,
    summary_rows: list[dict[str, object]],
    source_path: str,
    note: str,
) -> None:
    export_df, truncated = truncate_for_excel(df)
    export_df.to_excel(writer, sheet_name=sheet_name, index=False)
    format_sheet(writer.sheets[sheet_name])
    summary_rows.append(
        {
            "sheet_name": sheet_name,
            "source_path": source_path,
            "rows_in_source": int(len(df)),
            "rows_exported": int(len(export_df)),
            "columns": int(len(df.columns)),
            "truncated_for_excel_limit": truncated,
            "note": note,
        }
    )


def export_domain_review(output_path: Path | None = None) -> Path:
    repo_root = resolve_repo_root()
    processed_dir = repo_root / "data" / "processed"
    models_dir = repo_root / "models" / "domain"

    dataset_specs = [
        ("domain_model_dataset", processed_dir / "domain_model_dataset.parquet"),
        ("domain_train", processed_dir / "domain_train.parquet"),
        ("domain_val", processed_dir / "domain_val.parquet"),
        ("domain_test", processed_dir / "domain_test.parquet"),
    ]

    loaded_frames: list[tuple[str, Path, pd.DataFrame]] = []
    for dataset_name, path in dataset_specs:
        if path.exists():
            loaded_frames.append((dataset_name, path, pd.read_parquet(path)))

    model_frames = build_run_summary_frames(models_dir, "domain")
    if not loaded_frames and not model_frames:
        raise FileNotFoundError("No domain datasets or domain model outputs were found to export.")

    final_output_path = resolve_output_path(output_path, "domain_dataset_review")
    summary_rows: list[dict[str, object]] = []

    with pd.ExcelWriter(final_output_path, engine="openpyxl") as writer:
        if loaded_frames:
            overview_df = build_dataset_overview(loaded_frames)
            write_sheet(
                writer,
                "domain_dataset_overview",
                overview_df,
                summary_rows,
                str(processed_dir),
                "Generated summary for domain datasets.",
            )

            main_frame = next((df for name, _, df in loaded_frames if name == "domain_model_dataset"), None)
            if main_frame is not None:
                by_source_df = build_label_distribution(main_frame, "source", sort_desc=True)
                if not by_source_df.empty:
                    write_sheet(
                        writer,
                        "domain_by_source",
                        by_source_df,
                        summary_rows,
                        str(processed_dir / "domain_model_dataset.parquet"),
                        "Label distribution grouped by source.",
                    )

                by_date_df = build_label_distribution(main_frame, "collected_at", sort_desc=False)
                if not by_date_df.empty:
                    write_sheet(
                        writer,
                        "domain_by_date",
                        by_date_df,
                        summary_rows,
                        str(processed_dir / "domain_model_dataset.parquet"),
                        "Label distribution grouped by collected_at.",
                    )

                column_profile_df = build_column_profile(main_frame)
                write_sheet(
                    writer,
                    "domain_columns",
                    column_profile_df,
                    summary_rows,
                    str(processed_dir / "domain_model_dataset.parquet"),
                    "Column-level null and cardinality profile.",
                )

            for dataset_name, path, df in loaded_frames:
                write_sheet(
                    writer,
                    dataset_name,
                    df,
                    summary_rows,
                    str(path),
                    f"Raw export for {dataset_name}.",
                )

        for sheet_name, df in model_frames:
            write_sheet(
                writer,
                sheet_name,
                df,
                summary_rows,
                str(models_dir),
                "Domain model output.",
            )

        summary_df = pd.DataFrame(summary_rows)
        write_sheet(
            writer,
            "summary",
            summary_df,
            [],
            str(repo_root),
            "Workbook inventory.",
        )

    return final_output_path


def main() -> None:
    args = parse_args()
    output_path = export_domain_review(args.output)
    print(f"Domain review Excel file saved to: {output_path}")


if __name__ == "__main__":
    main()
