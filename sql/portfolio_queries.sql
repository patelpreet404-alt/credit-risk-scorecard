-- Portfolio exposure, approval mix, expected loss and delinquency monitoring.
-- Probability of default and loss-given-default must be calibrated to local definitions.

-- Snapshot KPIs at the application grain.
SELECT
    COUNT(*) AS applications,
    COUNT(*) FILTER (WHERE decision_status = 'Approved') AS approved_applications,
    SUM(requested_amount) FILTER (WHERE decision_status = 'Approved') AS approved_exposure,
    AVG(probability_default) FILTER (WHERE decision_status = 'Approved') AS mean_probability_default,
    SUM(requested_amount * probability_default * COALESCE(o.loss_given_default, 0.45))
        FILTER (WHERE decision_status = 'Approved') AS estimated_expected_loss
FROM application a
LEFT JOIN performance_outcome o USING (application_id)
WHERE application_date >= CURRENT_DATE - INTERVAL '12 months';

-- Default rate and scorecard discrimination by origination quarter.
SELECT
    DATE_TRUNC('quarter', a.application_date)::DATE AS origination_quarter,
    a.scorecard_version,
    COUNT(*) AS matured_accounts,
    AVG(o.default_12m::NUMERIC) AS observed_default_rate,
    AVG(a.probability_default) AS mean_predicted_default_probability
FROM application a
JOIN performance_outcome o USING (application_id)
WHERE o.observation_date >= a.application_date + INTERVAL '12 months'
  AND o.default_12m IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2;

-- Utilization segments and observed outcomes. Keep bin edges aligned with the scorecard.
SELECT
    CASE
        WHEN a.revolving_utilization < 0.20 THEN '<20%'
        WHEN a.revolving_utilization < 0.50 THEN '20–50%'
        WHEN a.revolving_utilization < 0.75 THEN '50–75%'
        ELSE '75%+'
    END AS utilization_band,
    COUNT(*) AS accounts,
    AVG(o.default_12m::NUMERIC) AS observed_default_rate,
    AVG(a.probability_default) AS mean_predicted_default_probability,
    SUM(o.exposure_at_default * o.loss_given_default) AS realized_loss
FROM application a
JOIN performance_outcome o USING (application_id)
GROUP BY 1
ORDER BY MIN(a.revolving_utilization);
