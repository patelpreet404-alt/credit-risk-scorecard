-- Portable analytical schema for a consumer credit application scorecard demo.
-- Adapt precision, date types, and access controls before use with lender data.
CREATE TABLE IF NOT EXISTS application (
    application_id       VARCHAR(40) PRIMARY KEY,
    customer_id          VARCHAR(40) NOT NULL,
    application_date     DATE NOT NULL,
    requested_amount     NUMERIC(14, 2) NOT NULL CHECK (requested_amount >= 0),
    annual_income        NUMERIC(14, 2) CHECK (annual_income >= 0),
    debt_to_income       NUMERIC(6, 5) CHECK (debt_to_income BETWEEN 0 AND 1),
    revolving_utilization NUMERIC(6, 5) CHECK (revolving_utilization BETWEEN 0 AND 1),
    credit_history_years NUMERIC(5, 2) CHECK (credit_history_years >= 0),
    delinquencies_12m    SMALLINT CHECK (delinquencies_12m >= 0),
    inquiries_6m         SMALLINT CHECK (inquiries_6m >= 0),
    term_months          SMALLINT,
    housing_status       VARCHAR(30),
    loan_purpose         VARCHAR(60),
    application_status   VARCHAR(24) NOT NULL,
    decision_status      VARCHAR(24),
    decision_date        DATE,
    scorecard_version    VARCHAR(30),
    credit_score         SMALLINT CHECK (credit_score BETWEEN 300 AND 850),
    probability_default  NUMERIC(8, 7) CHECK (probability_default BETWEEN 0 AND 1),
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_outcome (
    application_id       VARCHAR(40) PRIMARY KEY REFERENCES application(application_id),
    observation_date     DATE NOT NULL,
    default_12m          SMALLINT CHECK (default_12m IN (0, 1)),
    days_past_due_max    SMALLINT CHECK (days_past_due_max >= 0),
    exposure_at_default  NUMERIC(14, 2) CHECK (exposure_at_default >= 0),
    loss_given_default   NUMERIC(6, 5) CHECK (loss_given_default BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS scorecard_bin (
    scorecard_version VARCHAR(30) NOT NULL,
    feature_name      VARCHAR(100) NOT NULL,
    bin_label         VARCHAR(120) NOT NULL,
    lower_bound       NUMERIC(18, 6),
    upper_bound       NUMERIC(18, 6),
    woe               NUMERIC(12, 8) NOT NULL,
    information_value NUMERIC(12, 8) NOT NULL,
    effective_from    DATE NOT NULL,
    effective_to      DATE,
    PRIMARY KEY (scorecard_version, feature_name, bin_label, effective_from)
);

CREATE TABLE IF NOT EXISTS model_validation (
    validation_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scorecard_version VARCHAR(30) NOT NULL,
    validation_date  DATE NOT NULL,
    sample_name      VARCHAR(100) NOT NULL,
    sample_rows      INTEGER NOT NULL CHECK (sample_rows > 0),
    roc_auc          NUMERIC(6, 5),
    ks_statistic     NUMERIC(6, 5),
    gini_coefficient NUMERIC(6, 5),
    population_stability_index NUMERIC(8, 5),
    dataset_is_synthetic BOOLEAN NOT NULL DEFAULT FALSE,
    notes            TEXT
);

CREATE INDEX IF NOT EXISTS idx_application_date ON application(application_date);
CREATE INDEX IF NOT EXISTS idx_application_segment ON application(decision_status, scorecard_version);
CREATE INDEX IF NOT EXISTS idx_performance_observation ON performance_outcome(observation_date);
