"""Train an interpretable WOE logistic scorecard and export validation artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split

TARGET = "default_12m"
NUMERIC = [
    "annual_income",
    "debt_to_income",
    "revolving_utilization",
    "credit_history_years",
    "delinquencies_12m",
    "inquiries_6m",
    "loan_amount",
    "term_months",
    "employment_years",
]
CATEGORICAL = ["housing_status", "loan_purpose"]


def ks_statistic(y_true: pd.Series, probabilities: np.ndarray) -> float:
    fpr, tpr, _ = roc_curve(y_true, probabilities)
    return float(np.max(tpr - fpr))


def calculate_woe_iv(frame: pd.DataFrame, feature: str, target: str, bins: int = 5) -> dict:
    values = frame[feature]
    if pd.api.types.is_numeric_dtype(values) and values.nunique() > bins:
        grouped = pd.qcut(values, q=bins, duplicates="drop")
    else:
        grouped = values.astype("string").fillna("Missing")
    table = pd.DataFrame({"bin": grouped, "target": frame[target]}).groupby("bin", observed=False)["target"].agg(["sum", "count"])
    table["bad"] = table["sum"]
    table["good"] = table["count"] - table["bad"]
    eps = 0.5
    dist_good = (table["good"] + eps) / (table["good"].sum() + eps * len(table))
    dist_bad = (table["bad"] + eps) / (table["bad"].sum() + eps * len(table))
    table["woe"] = np.log(dist_good / dist_bad)
    table["iv_component"] = (dist_good - dist_bad) * table["woe"]
    return {
        "information_value": float(table["iv_component"].sum()),
        "bins": [
            {
                "bin": str(index),
                "good": int(row["good"]),
                "bad": int(row["bad"]),
                "woe": float(row["woe"]),
                "iv_component": float(row["iv_component"]),
            }
            for index, row in table.iterrows()
        ],
    }


def fit_woe_encode(
    train: pd.DataFrame,
    test: pd.DataFrame,
    y_train: pd.Series,
    feature: str,
    bins: int = 5,
) -> tuple[pd.Series, pd.Series, dict]:
    """Fit feature bins on training rows only, then apply the learned WOE map."""
    values = train[feature]
    if pd.api.types.is_numeric_dtype(values) and values.nunique() > bins:
        _, inner_edges = pd.qcut(values, q=bins, retbins=True, duplicates="drop")
        edges = np.concatenate(([-np.inf], inner_edges[1:-1], [np.inf]))
        train_bins = pd.cut(values, bins=edges, include_lowest=True)
        test_bins = pd.cut(test[feature], bins=edges, include_lowest=True)
    else:
        train_bins = values.astype("string").fillna("Missing")
        test_bins = test[feature].astype("string").fillna("Missing")

    table = pd.DataFrame({"bin": train_bins.astype("string"), "target": y_train.to_numpy()})
    counts = table.groupby("bin", dropna=False)["target"].agg(["sum", "count"])
    counts["bad"] = counts["sum"]
    counts["good"] = counts["count"] - counts["bad"]
    eps = 0.5
    good_dist = (counts["good"] + eps) / (counts["good"].sum() + eps * len(counts))
    bad_dist = (counts["bad"] + eps) / (counts["bad"].sum() + eps * len(counts))
    woe_map = np.log(good_dist / bad_dist).to_dict()
    fallback = float(np.mean(list(woe_map.values())))
    train_woe = train_bins.astype("string").map(woe_map).fillna(fallback).astype(float)
    test_woe = test_bins.astype("string").map(woe_map).fillna(fallback).astype(float)
    return train_woe, test_woe, {"edges": edges.tolist() if pd.api.types.is_numeric_dtype(values) and values.nunique() > bins else None, "woe_by_bin": {str(key): float(value) for key, value in woe_map.items()}, "unknown_bin_fallback": fallback}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/synthetic_applications.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    if not args.input.exists():
        parser.error(f"Input file not found: {args.input}. Generate a local synthetic sample first.")
    frame = pd.read_csv(args.input)
    required = set(NUMERIC + CATEGORICAL + [TARGET])
    missing = sorted(required.difference(frame.columns))
    if missing:
        parser.error(f"Input is missing required columns: {', '.join(missing)}")
    if frame[TARGET].nunique() != 2:
        parser.error(f"{TARGET} must contain both 0 and 1 outcomes")

    x_train, x_test, y_train, y_test = train_test_split(
        frame[NUMERIC + CATEGORICAL], frame[TARGET], test_size=0.25,
        random_state=494, stratify=frame[TARGET]
    )
    train_woe = pd.DataFrame(index=x_train.index)
    test_woe = pd.DataFrame(index=x_test.index)
    fitted_bins = {}
    for feature in NUMERIC + CATEGORICAL:
        train_woe[feature], test_woe[feature], fitted_bins[feature] = fit_woe_encode(
            x_train, x_test, y_train, feature
        )

    model = LogisticRegression(max_iter=1_000, class_weight="balanced", C=0.8)
    model.fit(train_woe, y_train)
    probabilities = model.predict_proba(test_woe)[:, 1]
    auc = roc_auc_score(y_test, probabilities)
    ks = ks_statistic(y_test, probabilities)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    validation = {
        "dataset": args.input.name,
        "synthetic_data": "synthetic" in args.input.name.lower(),
        "rows": int(len(frame)),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "default_rate": float(frame[TARGET].mean()),
        "roc_auc": float(auc),
        "ks_statistic": ks,
        "model": "LogisticRegression(class_weight='balanced', C=0.8)",
        "warning": "Synthetic-data metrics are for pipeline validation only; they are not evidence of real portfolio performance.",
    }
    (args.output_dir / "validation_metrics.json").write_text(json.dumps(validation, indent=2) + "\n")
    woe = {feature: calculate_woe_iv(pd.concat([x_train[feature], y_train], axis=1), feature, TARGET) for feature in NUMERIC + CATEGORICAL}
    (args.output_dir / "woe_iv.json").write_text(json.dumps(woe, indent=2) + "\n")
    (args.output_dir / "scorecard_bins.json").write_text(json.dumps(fitted_bins, indent=2) + "\n")
    scorecard = {
        "model": validation["model"],
        "features": NUMERIC + CATEGORICAL,
        "intercept": float(model.intercept_[0]),
        "coefficients": {feature: float(coef) for feature, coef in zip(NUMERIC + CATEGORICAL, model.coef_[0], strict=True)},
        "warning": "This fitted synthetic-data scorecard is for local pipeline demonstration only.",
    }
    (args.output_dir / "scorecard.json").write_text(json.dumps(scorecard, indent=2) + "\n")
    try:
        import statsmodels.api as sm

        stats = sm.Logit(y_train.to_numpy(), sm.add_constant(train_woe.to_numpy())).fit(disp=False, maxiter=200)
        summary = {"feature_names": ["intercept", *train_woe.columns.tolist()], "coefficients": stats.params.tolist(), "p_values": stats.pvalues.tolist()}
        (args.output_dir / "coefficient_diagnostics.json").write_text(json.dumps(summary, indent=2) + "\n")
    except (ImportError, AttributeError, ValueError, np.linalg.LinAlgError) as error:
        (args.output_dir / "coefficient_diagnostics.json").write_text(json.dumps({"available": False, "reason": str(error)}, indent=2) + "\n")

    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
