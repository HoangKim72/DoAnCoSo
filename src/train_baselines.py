from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

try:
    from xgboost import XGBClassifier
except ImportError:  # pragma: no cover - depends on optional dependency
    XGBClassifier = None

from phishing_url_ml.feature_engineering import build_feature_frame
from phishing_url_ml.settings import MODELS_DIR, PROCESSED_DIR
from phishing_url_ml.utils import log, require_columns


RANDOM_STATE = 42
MODEL_ORDER = [
    "logistic_regression",
    "linear_svm",
    "random_forest",
    "xgboost",
    "ann_mlp",
    "hybrid_lr_xgboost_ann",
]


def class_distribution(df: pd.DataFrame) -> dict[str, int]:
    counts = df["label"].value_counts().sort_index().to_dict()
    return {
        "benign": int(counts.get(0, 0)),
        "phishing": int(counts.get(1, 0)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and compare baseline phishing detection models.")
    parser.add_argument(
        "--dataset-kind",
        choices=["domain", "url"],
        default="domain",
        help="Dataset type to train on.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Optional path to the dataset parquet file.",
    )
    parser.add_argument(
        "--selection-metric",
        choices=["f1", "precision", "recall", "roc_auc", "pr_auc"],
        default="pr_auc",
        help="Validation metric used to choose the best model.",
    )
    parser.add_argument(
        "--write-splits",
        action="store_true",
        help="Also write temporal train/val/test parquet splits into data/processed.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory used to save metrics and the selected model.",
    )
    parser.add_argument(
        "--domain-balance-strategy",
        choices=["per_date_under", "global_under", "none"],
        default="per_date_under",
        help=(
            "Class-balancing strategy for the domain dataset before temporal split. "
            "Ignored for URL training."
        ),
    )
    return parser.parse_args()


def resolve_input_path(dataset_kind: str, input_path: Path | None) -> Path:
    if input_path is not None:
        return input_path
    return PROCESSED_DIR / f"{dataset_kind}_model_dataset.parquet"


def make_scaled_prefix() -> list[tuple[str, object]]:
    return [
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ]


def build_logistic_regression_pipeline() -> Pipeline:
    return Pipeline(
        make_scaled_prefix()
        + [
            (
                "model",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=RANDOM_STATE,
                    solver="liblinear",
                ),
            )
        ]
    )


def build_linear_svm_pipeline() -> Pipeline:
    return Pipeline(
        make_scaled_prefix()
        + [
            (
                "model",
                LinearSVC(
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            )
        ]
    )


def build_random_forest_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=400,
                    class_weight="balanced_subsample",
                    n_jobs=-1,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def build_xgboost_pipeline() -> Pipeline:
    if XGBClassifier is None:
        raise ImportError(
            "xgboost is not installed. Install project dependencies again after updating "
            "requirements.txt before training the xgboost or hybrid models."
        )
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                XGBClassifier(
                    objective="binary:logistic",
                    eval_metric="logloss",
                    n_estimators=300,
                    max_depth=6,
                    learning_rate=0.05,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    reg_lambda=1.0,
                    tree_method="hist",
                    n_jobs=-1,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def build_ann_mlp_pipeline() -> Pipeline:
    return Pipeline(
        make_scaled_prefix()
        + [
            (
                "model",
                MLPClassifier(
                    hidden_layer_sizes=(128, 64),
                    activation="relu",
                    solver="adam",
                    alpha=1e-4,
                    learning_rate_init=1e-3,
                    max_iter=300,
                    early_stopping=True,
                    validation_fraction=0.1,
                    n_iter_no_change=15,
                    random_state=RANDOM_STATE,
                ),
            )
        ]
    )


def build_hybrid_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "model",
                VotingClassifier(
                    estimators=[
                        ("logistic_regression", build_logistic_regression_pipeline()),
                        ("xgboost", build_xgboost_pipeline()),
                        ("ann_mlp", build_ann_mlp_pipeline()),
                    ],
                    voting="soft",
                ),
            )
        ]
    )


def build_model_pipelines() -> dict[str, Pipeline]:
    return {
        "logistic_regression": build_logistic_regression_pipeline(),
        "linear_svm": build_linear_svm_pipeline(),
        "random_forest": build_random_forest_pipeline(),
        "xgboost": build_xgboost_pipeline(),
        "ann_mlp": build_ann_mlp_pipeline(),
        "hybrid_lr_xgboost_ann": build_hybrid_pipeline(),
    }


def compute_split_sizes(num_dates: int) -> tuple[int, int, int]:
    train_days = max(1, int(round(num_dates * 0.7)))
    val_days = max(1, int(round(num_dates * 0.15)))
    test_days = num_dates - train_days - val_days
    if test_days < 1:
        test_days = 1
        if train_days >= val_days and train_days > 1:
            train_days -= 1
        else:
            val_days -= 1
    if val_days < 1:
        val_days = 1
        train_days = max(1, train_days - 1)
    return train_days, val_days, test_days


def temporal_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dates = sorted(pd.to_datetime(df["collected_at"]).dt.strftime("%Y-%m-%d").unique())
    if len(dates) < 3:
        raise ValueError(
            "Temporal split needs at least 3 distinct collection dates. "
            "Collect more daily snapshots before training baselines."
        )

    train_days, val_days, test_days = compute_split_sizes(len(dates))
    train_dates = set(dates[:train_days])
    val_dates = set(dates[train_days : train_days + val_days])
    test_dates = set(dates[train_days + val_days : train_days + val_days + test_days])

    train_df = df[df["collected_at"].isin(train_dates)].copy()
    val_df = df[df["collected_at"].isin(val_dates)].copy()
    test_df = df[df["collected_at"].isin(test_dates)].copy()
    return train_df, val_df, test_df


def drop_single_class_dates(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    labels_per_date = (
        df.groupby("collected_at")["label"]
        .agg(lambda values: tuple(sorted(set(int(value) for value in values))))
        .to_dict()
    )
    dropped_dates = [day for day, labels in labels_per_date.items() if labels != (0, 1)]
    if not dropped_dates:
        return df, []
    filtered = df.loc[~df["collected_at"].isin(dropped_dates)].copy()
    return filtered, sorted(dropped_dates)


def balance_domain_dataset_per_date(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    balanced_frames: list[pd.DataFrame] = []
    per_date_rows: list[dict[str, object]] = []

    for offset, (collected_at, date_df) in enumerate(df.groupby("collected_at", sort=True)):
        counts = date_df["label"].value_counts().sort_index()
        benign_count = int(counts.get(0, 0))
        phishing_count = int(counts.get(1, 0))
        if benign_count == 0 or phishing_count == 0:
            raise ValueError(
                "Domain balancing expects every retained date to contain both classes. "
                f"Date {collected_at} has benign={benign_count}, phishing={phishing_count}."
            )

        target_count = min(benign_count, phishing_count)
        sampled_parts = []
        for label in [0, 1]:
            label_df = date_df.loc[date_df["label"] == label]
            if len(label_df) > target_count:
                label_df = label_df.sample(n=target_count, random_state=RANDOM_STATE + offset + label)
            sampled_parts.append(label_df)

        balanced_date_df = pd.concat(sampled_parts, ignore_index=True)
        balanced_date_df = balanced_date_df.sort_values(["collected_at", "label"], ascending=[True, False])
        balanced_frames.append(balanced_date_df)
        per_date_rows.append(
            {
                "collected_at": str(collected_at),
                "original_benign": benign_count,
                "original_phishing": phishing_count,
                "balanced_benign": target_count,
                "balanced_phishing": target_count,
                "rows_removed": (benign_count + phishing_count) - (target_count * 2),
            }
        )

    balanced_df = pd.concat(balanced_frames, ignore_index=True)
    balanced_df = balanced_df.sort_values(["collected_at", "label"], ascending=[True, False]).reset_index(drop=True)
    summary = {
        "strategy": "per_date_under",
        "rows_before": int(len(df)),
        "rows_after": int(len(balanced_df)),
        "class_distribution_before": class_distribution(df),
        "class_distribution_after": class_distribution(balanced_df),
        "per_date": per_date_rows,
    }
    return balanced_df, summary


def balance_domain_dataset_globally(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    counts = df["label"].value_counts().sort_index()
    benign_count = int(counts.get(0, 0))
    phishing_count = int(counts.get(1, 0))
    if benign_count == 0 or phishing_count == 0:
        raise ValueError(
            "Global domain balancing needs both classes to be present before temporal split."
        )

    target_count = min(benign_count, phishing_count)
    sampled_parts = []
    for label in [0, 1]:
        label_df = df.loc[df["label"] == label]
        if len(label_df) > target_count:
            label_df = label_df.sample(n=target_count, random_state=RANDOM_STATE + label)
        sampled_parts.append(label_df)

    balanced_df = pd.concat(sampled_parts, ignore_index=True)
    balanced_df = balanced_df.sort_values(["collected_at", "label"], ascending=[True, False]).reset_index(drop=True)
    summary = {
        "strategy": "global_under",
        "rows_before": int(len(df)),
        "rows_after": int(len(balanced_df)),
        "class_distribution_before": class_distribution(df),
        "class_distribution_after": class_distribution(balanced_df),
        "target_count_per_class": target_count,
    }
    return balanced_df, summary


def apply_domain_balance_strategy(
    df: pd.DataFrame,
    strategy: str,
) -> tuple[pd.DataFrame, dict[str, object] | None]:
    if strategy == "none":
        return (
            df,
            {
                "strategy": "none",
                "rows_before": int(len(df)),
                "rows_after": int(len(df)),
                "class_distribution_before": class_distribution(df),
                "class_distribution_after": class_distribution(df),
            },
        )
    if strategy == "per_date_under":
        return balance_domain_dataset_per_date(df)
    if strategy == "global_under":
        return balance_domain_dataset_globally(df)
    raise ValueError(f"Unsupported domain balance strategy: {strategy}")


def validate_binary_labels(df: pd.DataFrame, split_name: str) -> None:
    unique_labels = sorted(df["label"].unique())
    if unique_labels != [0, 1]:
        raise ValueError(
            f"{split_name} split must contain both classes 0 and 1, but found {unique_labels}. "
            "Collect more data or revise the source mix."
        )


def scores_for_model(model: Pipeline, features: pd.DataFrame) -> pd.Series:
    estimator = model.named_steps["model"]
    transformed = model[:-1].transform(features) if len(model.steps) > 1 else features
    if hasattr(estimator, "predict_proba"):
        return pd.Series(estimator.predict_proba(transformed)[:, 1], index=features.index)
    if hasattr(estimator, "decision_function"):
        return pd.Series(estimator.decision_function(transformed), index=features.index)
    raise TypeError("Model does not support predict_proba or decision_function.")


def evaluate_predictions(y_true: pd.Series, y_pred: pd.Series, scores: pd.Series) -> dict[str, float]:
    return {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "pr_auc": float(average_precision_score(y_true, scores)),
    }


def save_splits(dataset_kind: str, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    paths = {
        "train": PROCESSED_DIR / f"{dataset_kind}_train.parquet",
        "val": PROCESSED_DIR / f"{dataset_kind}_val.parquet",
        "test": PROCESSED_DIR / f"{dataset_kind}_test.parquet",
    }
    for split_name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        split_df.to_parquet(paths[split_name], index=False)
        log(f"Wrote {dataset_kind} {split_name} split to {paths[split_name]}")


def sort_model_metrics(metrics_df: pd.DataFrame, selection_metric: str) -> pd.DataFrame:
    ordered = metrics_df.copy()
    ordered["model"] = pd.Categorical(ordered["model"], categories=MODEL_ORDER, ordered=True)
    ordered = ordered.sort_values([selection_metric, "model"], ascending=[False, True]).reset_index(drop=True)
    ordered["model"] = ordered["model"].astype(str)
    return ordered


def build_model_comparison(
    validation_df: pd.DataFrame,
    test_df: pd.DataFrame,
    best_model_name: str,
    selection_metric: str,
) -> pd.DataFrame:
    merged = validation_df.merge(test_df, on="model", suffixes=("_validation", "_test"))
    merged.insert(1, "is_selected_model", merged["model"].eq(best_model_name))
    return sort_model_metrics(merged, f"{selection_metric}_validation")


def metrics_records(metrics_df: pd.DataFrame) -> list[dict[str, object]]:
    return json.loads(metrics_df.to_json(orient="records"))


def main() -> None:
    args = parse_args()
    input_path = resolve_input_path(args.dataset_kind, args.input)
    output_dir = args.output_dir or (MODELS_DIR / args.dataset_kind)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(input_path)
    require_columns(df, ["sample_text", "label", "collected_at"], dataset_name="model dataset")
    if df["label"].nunique() < 2:
        raise SystemExit(
            "The selected dataset has fewer than 2 classes. Build a dataset with both phishing "
            "and benign samples before training."
        )

    raw_class_distribution = class_distribution(df)
    balancing_summary: dict[str, object] | None = None
    df, dropped_dates = drop_single_class_dates(df)
    if dropped_dates:
        log(
            "Dropping collection dates without both classes before temporal split: "
            + ", ".join(dropped_dates)
        )
    if df["collected_at"].nunique() < 3:
        raise SystemExit(
            "After dropping dates that only contain one class, fewer than 3 collection dates remain. "
            "Collect more daily snapshots or revise the source mix."
        )

    if args.dataset_kind == "domain":
        df, balancing_summary = apply_domain_balance_strategy(df, args.domain_balance_strategy)
        balanced_distribution = class_distribution(df)
        log(
            "Balanced domain dataset before temporal split: "
            f"strategy={args.domain_balance_strategy}, "
            f"benign={balanced_distribution['benign']:,}, phishing={balanced_distribution['phishing']:,}"
        )

    train_df, val_df, test_df = temporal_split(df)
    validate_binary_labels(train_df, "train")
    validate_binary_labels(val_df, "validation")
    validate_binary_labels(test_df, "test")
    if args.write_splits:
        save_splits(args.dataset_kind, train_df, val_df, test_df)

    x_train = build_feature_frame(train_df, args.dataset_kind)
    x_val = build_feature_frame(val_df, args.dataset_kind)
    y_train = train_df["label"].astype(int)
    y_val = val_df["label"].astype(int)
    model_pipelines = build_model_pipelines()

    validation_rows = []
    for model_name, model in model_pipelines.items():
        model.fit(x_train, y_train)
        val_pred = pd.Series(model.predict(x_val), index=val_df.index)
        val_scores = scores_for_model(model, x_val)
        metrics = evaluate_predictions(y_val, val_pred, val_scores)
        validation_rows.append({"model": model_name, **metrics})
        log(
            f"Validation metrics for {model_name}: "
            f"precision={metrics['precision']:.4f}, recall={metrics['recall']:.4f}, "
            f"f1={metrics['f1']:.4f}, pr_auc={metrics['pr_auc']:.4f}"
        )

    validation_df = sort_model_metrics(pd.DataFrame(validation_rows), args.selection_metric)
    best_model_name = str(validation_df.iloc[0]["model"])
    log(f"Selected best model by {args.selection_metric}: {best_model_name}")

    train_val_df = pd.concat([train_df, val_df], ignore_index=True)
    x_train_val = build_feature_frame(train_val_df, args.dataset_kind)
    y_train_val = train_val_df["label"].astype(int)
    x_test = build_feature_frame(test_df, args.dataset_kind)
    y_test = test_df["label"].astype(int)

    best_model = None
    test_rows = []
    for model_name, model in build_model_pipelines().items():
        model.fit(x_train_val, y_train_val)
        test_pred = pd.Series(model.predict(x_test), index=test_df.index)
        test_scores = scores_for_model(model, x_test)
        metrics = evaluate_predictions(y_test, test_pred, test_scores)
        test_rows.append({"model": model_name, **metrics})
        log(
            f"Test metrics for {model_name}: "
            f"precision={metrics['precision']:.4f}, recall={metrics['recall']:.4f}, "
            f"f1={metrics['f1']:.4f}, pr_auc={metrics['pr_auc']:.4f}"
        )
        if model_name == best_model_name:
            best_model = model

    if best_model is None:
        raise RuntimeError(f"Selected best model {best_model_name} was not retrained successfully.")

    test_results_df = sort_model_metrics(pd.DataFrame(test_rows), args.selection_metric)
    model_comparison_df = build_model_comparison(validation_df, test_results_df, best_model_name, args.selection_metric)
    test_metrics = next(
        row for row in metrics_records(test_results_df) if row["model"] == best_model_name
    ).copy()
    test_metrics.pop("model", None)

    validation_path = output_dir / "validation_metrics.csv"
    validation_df.to_csv(validation_path, index=False)
    log(f"Wrote validation metrics to {validation_path}")

    test_metrics_path = output_dir / "test_metrics.csv"
    test_results_df.to_csv(test_metrics_path, index=False)
    log(f"Wrote test metrics to {test_metrics_path}")

    model_comparison_path = output_dir / "model_comparison.csv"
    model_comparison_df.to_csv(model_comparison_path, index=False)
    log(f"Wrote model comparison to {model_comparison_path}")

    model_path = output_dir / f"{best_model_name}.joblib"
    joblib.dump(best_model, model_path)
    log(f"Saved selected model to {model_path}")

    summary_path = output_dir / "run_summary.json"
    summary = {
        "dataset_kind": args.dataset_kind,
        "input_path": str(input_path),
        "selection_metric": args.selection_metric,
        "best_model": best_model_name,
        "candidate_models": list(model_pipelines.keys()),
        "domain_balance_strategy": args.domain_balance_strategy if args.dataset_kind == "domain" else None,
        "class_distribution_before_processing": raw_class_distribution,
        "class_distribution_after_processing": class_distribution(df),
        "balancing": balancing_summary,
        "validation_results": metrics_records(validation_df),
        "test_results": metrics_records(test_results_df),
        "test_metrics": test_metrics,
        "split_rows": {
            "train": int(len(train_df)),
            "validation": int(len(val_df)),
            "test": int(len(test_df)),
        },
        "split_dates": {
            "train": sorted(train_df["collected_at"].unique().tolist()),
            "validation": sorted(val_df["collected_at"].unique().tolist()),
            "test": sorted(test_df["collected_at"].unique().tolist()),
        },
        "dropped_single_class_dates": dropped_dates,
        "artifacts": {
            "validation_metrics_csv": str(validation_path),
            "test_metrics_csv": str(test_metrics_path),
            "model_comparison_csv": str(model_comparison_path),
            "selected_model_path": str(model_path),
        },
        "feature_columns": build_feature_frame(df.head(1), args.dataset_kind).columns.tolist(),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log(f"Wrote run summary to {summary_path}")
    log(
        f"Test metrics for selected model {best_model_name}: "
        f"precision={test_metrics['precision']:.4f}, recall={test_metrics['recall']:.4f}, "
        f"f1={test_metrics['f1']:.4f}, pr_auc={test_metrics['pr_auc']:.4f}"
    )


if __name__ == "__main__":
    main()
