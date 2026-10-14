"""Create a reproducible, synthetic credit application sample for local development."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def generate(rows: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    income = np.clip(rng.lognormal(np.log(58_000), 0.55, rows), 15_000, 250_000)
    dti = np.clip(rng.beta(2.1, 4.2, rows) * 0.82, 0.01, 0.92)
    utilization = np.clip(rng.beta(2.0, 2.8, rows), 0.01, 0.99)
    history_years = np.clip(rng.gamma(3.0, 3.0, rows), 0, 35)
    delinquencies = np.clip(rng.poisson(0.36, rows), 0, 6)
    inquiries = np.clip(rng.poisson(1.1, rows), 0, 8)
    loan_amount = np.clip(income * rng.uniform(0.08, 0.72, rows), 1_000, 100_000)
    term_months = rng.choice([36, 48, 60, 72], rows, p=[0.28, 0.2, 0.38, 0.14])
    employment_years = np.clip(rng.gamma(2.0, 2.2, rows), 0, 35)
    housing = rng.choice(["Mortgage", "Rent", "Own"], rows, p=[0.44, 0.4, 0.16])
    purpose = rng.choice(["Debt consolidation", "Auto", "Home improvement", "Major purchase"], rows)

    # The target is intentionally generated from known signals. It creates useful
    # test data, not an empirical estimate of any lender's default behavior.
    log_odds = (
        -3.1
        + 3.0 * dti
        + 2.0 * utilization
        + 0.42 * delinquencies
        + 0.18 * inquiries
        - 0.035 * history_years
        - 0.018 * employment_years
        + 0.35 * (housing == "Rent")
        + 0.28 * (term_months >= 60)
        + rng.normal(0, 0.52, rows)
    )
    probability = 1 / (1 + np.exp(-log_odds))
    default_12m = rng.binomial(1, probability)

    return pd.DataFrame(
        {
            "application_id": [f"DEMO-{i:06d}" for i in range(1, rows + 1)],
            "annual_income": income.round(2),
            "debt_to_income": dti.round(4),
            "revolving_utilization": utilization.round(4),
            "credit_history_years": history_years.round(1),
            "delinquencies_12m": delinquencies,
            "inquiries_6m": inquiries,
            "loan_amount": loan_amount.round(2),
            "term_months": term_months,
            "employment_years": employment_years.round(1),
            "housing_status": housing,
            "loan_purpose": purpose,
            "default_12m": default_12m,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=494)
    parser.add_argument("--output", type=Path, default=Path("data/synthetic_applications.csv"))
    args = parser.parse_args()
    if args.rows < 100:
        parser.error("--rows must be at least 100")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame = generate(args.rows, args.seed)
    frame.to_csv(args.output, index=False)
    print(f"Wrote {len(frame):,} synthetic demo applications to {args.output}")
    print(f"Synthetic 12-month default prevalence: {frame['default_12m'].mean():.2%}")


if __name__ == "__main__":
    main()
