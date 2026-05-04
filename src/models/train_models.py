from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    auc,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_curve,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from feature_engineering import FEATURE_COLUMNS, TARGET_COLUMN

FIGURE_DPI = 150
TEST_FRACTION = 0.2
RANDOM_STATE = 42


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_featured_data(featured_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(featured_csv)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)


def add_ticker_dummies(df: pd.DataFrame) -> pd.DataFrame:
    encoded_df = df.copy()
    ticker_dummies = pd.get_dummies(encoded_df["ticker"], prefix="ticker", dtype=int)
    return pd.concat([encoded_df, ticker_dummies], axis=1)


def chronological_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_parts: list[pd.DataFrame] = []
    test_parts: list[pd.DataFrame] = []

    for _, group in df.groupby("ticker", sort=True):
        split_idx = max(1, int(len(group) * (1 - TEST_FRACTION)))
        split_idx = min(split_idx, len(group) - 1)
        train_parts.append(group.iloc[:split_idx].copy())
        test_parts.append(group.iloc[split_idx:].copy())

    train_df = pd.concat(train_parts, ignore_index=True)
    test_df = pd.concat(test_parts, ignore_index=True)
    return train_df, test_df


def feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    ticker_columns = sorted(column for column in df.columns if column.startswith("ticker_"))
    model_columns = FEATURE_COLUMNS + ticker_columns
    return df[model_columns].copy(), df[TARGET_COLUMN].copy()


def model_registry() -> dict[str, object]:
    return {
        "logistic_regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        ),
        "decision_tree": DecisionTreeClassifier(
            max_depth=5,
            min_samples_leaf=10,
            random_state=RANDOM_STATE,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=10,
            random_state=RANDOM_STATE,
        ),
    }


def evaluate_predictions(y_true: pd.Series, y_pred) -> dict[str, float]:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }


def compute_naive_baseline(
    y_train: pd.Series, y_test: pd.Series,
) -> tuple[dict[str, float | int | str], np.ndarray]:
    majority_class = int(y_train.mode().iloc[0])
    y_pred = np.full(len(y_test), majority_class)
    metrics = evaluate_predictions(y_test, y_pred)
    row = {
        "model": "naive_baseline",
        "train_rows": len(y_train),
        "test_rows": len(y_test),
        **{metric: round(value, 4) for metric, value in metrics.items()},
    }
    return row, y_pred


def save_confusion_matrix_csv(
    y_true: pd.Series,
    y_pred,
    output_path: Path,
) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    matrix_df = pd.DataFrame(
        matrix,
        index=["actual_down", "actual_up"],
        columns=["predicted_down", "predicted_up"],
    )
    matrix_df.to_csv(output_path)


def save_classification_report_csv(
    y_true: pd.Series,
    y_pred,
    output_path: Path,
) -> None:
    report = classification_report(
        y_true, y_pred, target_names=["down", "up"], output_dict=True,
    )
    report_df = pd.DataFrame(report).T.round(4)
    report_df.to_csv(output_path)


def save_feature_correlation_heatmap(df: pd.DataFrame, output_path: Path) -> None:
    corr = df[FEATURE_COLUMNS].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, linewidths=0.5)
    plt.title("Engineered Feature Correlation Heatmap")
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close()


def save_model_comparison_plot(results_df: pd.DataFrame, output_path: Path) -> None:
    plot_df = results_df.melt(
        id_vars="model",
        value_vars=["accuracy", "precision", "recall", "f1"],
        var_name="metric",
        value_name="score",
    )

    plt.figure(figsize=(12, 6))
    sns.barplot(data=plot_df, x="model", y="score", hue="metric")
    plt.ylim(0, 1)
    plt.title("Model Performance Comparison (Including Naive Baseline)")
    plt.xlabel("Model")
    plt.ylabel("Score")
    plt.xticks(rotation=10)
    plt.legend(title="Metric")
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close()


def save_feature_importance_plot(
    model: RandomForestClassifier,
    columns: list[str],
    output_path: Path,
) -> None:
    importance_df = (
        pd.DataFrame(
            {"feature": columns, "importance": model.feature_importances_}
        )
        .sort_values("importance", ascending=False)
        .head(12)
    )

    plt.figure(figsize=(10, 6))
    sns.barplot(data=importance_df, x="importance", y="feature", orient="h")
    plt.title("Random Forest Feature Importances")
    plt.xlabel("Importance")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close()


def save_roc_curves(
    trained_models: dict[str, object],
    X_test: pd.DataFrame,
    y_test: pd.Series,
    output_path: Path,
    auc_output_path: Path,
) -> None:
    plt.figure(figsize=(8, 8))
    auc_records: list[dict[str, str | float]] = []

    for model_name, model in trained_models.items():
        if hasattr(model, "predict_proba"):
            y_proba = model.predict_proba(X_test)[:, 1]
        elif hasattr(model, "decision_function"):
            y_proba = model.decision_function(X_test)
        else:
            continue
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        roc_auc = auc(fpr, tpr)
        display_name = model_name.replace("_", " ").title()
        plt.plot(fpr, tpr, linewidth=2, label=f"{display_name} (AUC = {roc_auc:.3f})")
        auc_records.append({"model": model_name, "auc": round(roc_auc, 4)})

    plt.plot([0, 1], [0, 1], "k--", linewidth=1, alpha=0.6, label="Random (AUC = 0.500)")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curves — Model Comparison")
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close()

    pd.DataFrame(auc_records).to_csv(auc_output_path, index=False)


def main() -> None:
    root = project_root()
    featured_csv = root / "data" / "processed" / "featured_stock_prices.csv"
    metrics_dir = root / "outputs" / "metrics"
    figures_dir = root / "outputs" / "figures"

    if not featured_csv.exists():
        raise FileNotFoundError(
            f"Missing featured dataset at {featured_csv}. Run feature_engineering.py first."
        )

    metrics_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style="whitegrid", font_scale=1.0)

    featured_df = add_ticker_dummies(load_featured_data(featured_csv))
    train_df, test_df = chronological_split(featured_df)
    X_train, y_train = feature_matrix(train_df)
    X_test, y_test = feature_matrix(test_df)

    baseline_row, baseline_preds = compute_naive_baseline(y_train, y_test)
    results: list[dict[str, float | int | str]] = [baseline_row]
    save_confusion_matrix_csv(
        y_test, baseline_preds, metrics_dir / "confusion_matrix_naive_baseline.csv",
    )

    trained_models: dict[str, object] = {}

    for model_name, model in model_registry().items():
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        metrics = evaluate_predictions(y_test, predictions)
        results.append(
            {
                "model": model_name,
                "train_rows": len(train_df),
                "test_rows": len(test_df),
                **{metric: round(value, 4) for metric, value in metrics.items()},
            }
        )
        save_confusion_matrix_csv(
            y_test, predictions, metrics_dir / f"confusion_matrix_{model_name}.csv",
        )
        save_classification_report_csv(
            y_test, predictions, metrics_dir / f"classification_report_{model_name}.csv",
        )
        trained_models[model_name] = model

    results_df = pd.DataFrame(results).sort_values("accuracy", ascending=False)
    results_df.to_csv(metrics_dir / "model_comparison.csv", index=False)

    save_feature_correlation_heatmap(
        featured_df, figures_dir / "feature_correlation_heatmap.png",
    )
    save_model_comparison_plot(results_df, figures_dir / "model_comparison.png")

    random_forest_model = trained_models["random_forest"]
    save_feature_importance_plot(
        random_forest_model,
        X_train.columns.tolist(),
        figures_dir / "feature_importance.png",
    )

    save_roc_curves(
        trained_models, X_test, y_test,
        figures_dir / "roc_curves.png",
        metrics_dir / "roc_auc_scores.csv",
    )

    print(f"Saved model comparison to {metrics_dir / 'model_comparison.csv'}")
    print(f"Saved classification reports to {metrics_dir}")
    print(f"Saved confusion matrices to {metrics_dir}")
    print(f"Saved ROC curves to {figures_dir / 'roc_curves.png'}")
    print(f"Saved ML figures to {figures_dir}")
    print(results_df.to_string(index=False))


if __name__ == "__main__":
    main()
