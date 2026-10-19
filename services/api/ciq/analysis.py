"""Small-sample analyses with explicit baselines and no future leakage."""

import math
import warnings
import numpy as np
from scipy import stats
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from .db import query
from .metrics import Scope


def fit_ets(values, horizon=1):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = ExponentialSmoothing(
            values,
            trend="add",
            damped_trend=True,
            seasonal="add",
            seasonal_periods=12,
            initialization_method="estimated",
        ).fit(optimized=True)
    return np.maximum(0, model.forecast(horizon))


def errors(actual, predicted):
    a, p = np.asarray(actual), np.asarray(predicted)
    nonzero = a != 0
    return {
        "mape": float(np.mean(np.abs((a[nonzero] - p[nonzero]) / a[nonzero])) * 100)
        if nonzero.any()
        else None,
        "wape": float(np.sum(abs(a - p)) / np.sum(abs(a)) * 100)
        if np.sum(abs(a))
        else None,
        "mae": float(np.mean(abs(a - p))),
        "zero_actuals": int((~nonzero).sum()),
    }


def analyze(country="All markets"):
    scope = Scope(country=country)
    clause = (
        "" if scope.country == "All markets" else f"WHERE country='{scope.country}'"
    )
    series = query(
        f"SELECT month,SUM(revenue) AS revenue FROM analytics.v_sales_monthly {clause} GROUP BY month ORDER BY month"
    )["rows"]
    y = np.array([r["revenue"] for r in series])
    validation = {"seasonal_naive": [], "ets": []}
    for t in range(30, 42):
        validation["seasonal_naive"].append(y[t - 12])
        validation["ets"].append(fit_ets(y[:t])[0])
    validation_metrics = {name: errors(y[30:42], p) for name, p in validation.items()}
    selected = min(validation_metrics, key=lambda name: validation_metrics[name]["mae"])
    test = {"seasonal_naive": [], "ets": []}
    for t in range(42, 48):
        test["seasonal_naive"].append(y[t - 12])
        test["ets"].append(fit_ets(y[:t])[0])
    test_metrics = {name: errors(y[42:], p) for name, p in test.items()}
    forecast = fit_ets(y, 3) if selected == "ets" else y[-12:-9]
    residuals = y[30:42] - np.array(validation[selected])
    # Exploratory residual band, not advertised as calibrated prediction coverage.
    spread = float(np.quantile(np.abs(residuals), 0.9))
    future = [
        {
            "month": f"2026-{m:02}-01",
            "forecast": round(float(v), 2),
            "lower": round(max(0, float(v) - spread), 2),
            "upper": round(float(v) + spread, 2),
        }
        for m, v in zip([10, 11, 12], forecast)
    ]
    change = y[12:] - y[:-12]
    historical = change[:-1]
    center = float(np.median(historical))
    mad = float(np.median(np.abs(historical - center)))
    score = float((change[-1] - center) / (1.4826 * mad)) if mad else None
    return {
        "country": country,
        "history": series,
        "forecast": future,
        "selected_model": selected,
        "validation": validation_metrics,
        "test": test_metrics,
        "test_period": "April–September 2026",
        "method": "Expanding-window one-month-ahead evaluation. Model selected on October 2025–March 2026 validation by MAE, then tested on six unseen months. Three-month future projections are exploratory.",
        "interval_note": "The shaded band uses validation absolute residuals; it is not a calibrated multi-horizon prediction interval.",
        "anomaly": {
            "month": series[-1]["month"],
            "robust_score": score,
            "flagged": bool(score is not None and score < -3),
            "method": "Latest year-over-year revenue difference compared with historical differences using median and MAD; threshold −3. No causal attribution.",
        },
    }


def promotion_analysis():
    sql = """SELECT territory,
    SUM(CASE WHEN month < '2025-04-01' THEN revenue ELSE 0 END) AS pre,
    SUM(CASE WHEN month >= '2025-04-01' THEN revenue ELSE 0 END) AS post,
    MAX(CAST(promotion AS INT)) AS treated
    FROM analytics.v_sales_monthly WHERE product='Immunex' AND month >= '2025-01-01' AND month <= '2025-06-01'
    GROUP BY territory ORDER BY territory"""
    rows = query(sql)["rows"]
    treated = np.array([r["post"] / r["pre"] - 1 for r in rows if r["treated"]])
    control = np.array([r["post"] / r["pre"] - 1 for r in rows if not r["treated"]])
    result = stats.permutation_test(
        (treated, control),
        lambda a, b: np.mean(a) - np.mean(b),
        permutation_type="independent",
        n_resamples=np.inf,
        alternative="two-sided",
    )
    se = math.sqrt(
        treated.var(ddof=1) / len(treated) + control.var(ddof=1) / len(control)
    )
    df = (
        treated.var(ddof=1) / len(treated) + control.var(ddof=1) / len(control)
    ) ** 2 / (
        (treated.var(ddof=1) / len(treated)) ** 2 / (len(treated) - 1)
        + (control.var(ddof=1) / len(control)) ** 2 / (len(control) - 1)
    )
    margin = stats.t.ppf(0.975, df) * se
    effect = float(result.statistic)
    return {
        "effect_pp": effect * 100,
        "p_value": float(result.pvalue),
        "ci_low_pp": float(effect - margin) * 100,
        "ci_high_pp": float(effect + margin) * 100,
        "treated_territories": len(treated),
        "control_territories": len(control),
        "method": "Difference in pre/post revenue growth, territory as the randomized unit; exact two-sided randomization test. Approximate 95% Welch interval.",
        "limitation": "A deliberately randomized synthetic experiment with 16 territories. This is a method demonstration, not evidence of real-world effectiveness.",
    }
