# Ledgerline product brief

Ledgerline is a portfolio-ready credit-risk assessment and scorecard demonstration aligned with the credit-risk project in Preet Patel's supplied resume. It brings portfolio monitoring, application review, interpretable WOE/IV analysis, macroeconomic sensitivity checks, and an applicant scoring sandbox into one analyst workspace.

## Audience and job

Credit risk analysts and hiring teams should be able to understand the portfolio's exposure, inspect how an interpretable scorecard separates risk, explore plausible loss sensitivity, and try a hypothetical application without confusing demo values for a live lending system.

## Product truth

- The resume brief states 50,000+ assessed applications, logistic regression with WOE and IV, AUC-ROC 0.84, KS statistic 48%, and expected-loss reporting.
- This workspace contains synthetic examples and illustrative portfolio outputs. It has no connected lender, production applicant dataset, or live decisioning service.
- The displayed validation values mirror the supplied brief. The training pipeline can compute metrics from a provided CSV; generated synthetic records are for development only and cannot substantiate real-world model performance.
- Never use the decision sandbox for a real lending decision.

## First surface

An operational dashboard for analysts: portfolio balance and expected loss first, then model health, recent application decisions, borrower-tier risk, and clear paths into model review and stress testing.

## Core flows

1. Scan portfolio exposure and model health.
2. Search and filter the application queue; export visible records.
3. Inspect feature IV and WOE bins and read the methodology.
4. Adjust macroeconomic assumptions and review illustrative loss sensitivity.
5. Score a hypothetical profile in a clearly labeled local sandbox.
