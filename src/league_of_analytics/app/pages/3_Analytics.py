"""Analytics page: logistic regression of win/loss on a player's in-game stats."""

import numpy as np
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
import streamlit as st
from ibis import _
from queries import player_rows, selected_player
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    log_loss,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.utils import resample
from statsmodels.stats.outliers_influence import variance_inflation_factor

DEFAULT_FEATURES = ["kills", "deaths", "assists", "wardsPlaced"]
EXTRA_FEATURES = [
    "detectorWardsPlaced",
    "firstBloodKill",
    "firstTowerKill",
    "damageDealtToObjectives",
    "damageDealtToTurrets",
    "totalMinionsKilled",
    "inhibitorKills",
    "nexusTakedowns",
]

EXPLANATION = """
Logistic regression models the probability of a binary outcome (win or lose) from
features such as kills, deaths, assists and wards placed.

- **Coefficients** show how strongly each feature pushes the chance of winning up or down.
- **Odds ratios** (exp of the coefficient) show how the odds change per one-unit increase.
  An odds ratio of 1.2 for assists means each extra assist raises the odds of winning by 20%.
- **Performance metrics** (accuracy, AUC, McFadden R², confusion matrix) show how well the model
  predicts outcomes on games it has not seen.
- **P-values** here come from bootstrapped standard errors; **VIF** flags features that overlap
  heavily (values above ~5-10 suggest multicollinearity).
"""


@st.cache_data
def load_data(name: str, tag: str, features: tuple[str, ...]) -> pd.DataFrame:
    """Win flag plus the chosen features for each of the player's games."""
    table = player_rows(name, tag).select(
        win=_.p.win.cast("int"),
        **{f: _.p[f].cast("int") for f in features},
    )
    return table.execute()


def bootstrap_coefficients(X, y, n_iterations: int = 1000):
    coefs = np.array(
        [LogisticRegression().fit(*resample(X, y)).coef_[0] for _ in range(n_iterations)]
    )
    return coefs.mean(axis=0), coefs.std(axis=0)


@st.cache_data
def run_regression(data: pd.DataFrame) -> dict:
    X, y = data.drop(columns="win"), data["win"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = LogisticRegression().fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    # Confusion matrix: rows = actual (negative, positive), columns = predicted
    (tn, fp), (fn, tp) = confusion_matrix(y_test, y_pred, labels=[0, 1])
    conf_matrix = ff.create_annotated_heatmap(
        z=[[tn, fp], [fn, tp]],
        x=["Predicted Negative", "Predicted Positive"],
        y=["Actual Negative", "Actual Positive"],
        annotation_text=[[f"True negative {tn}", f"False positive {fp}"],
                         [f"False negative {fn}", f"True positive {tp}"]],
        colorscale="Viridis",
    )

    fpr, tpr, _thresholds = roc_curve(y_test, y_prob)
    auc = roc_auc_score(y_test, y_prob)
    roc = go.Figure(go.Scatter(x=fpr, y=tpr, mode="lines", name=f"ROC (AUC = {auc:.2f})"))
    roc.add_shape(type="line", x0=0, y0=0, x1=1, y1=1, line=dict(color="grey", dash="dash"))
    roc.update_layout(
        title="ROC curve",
        xaxis_title="False positive rate",
        yaxis_title="True positive rate",
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1]),
    )

    # McFadden R2 on the test set: fitted model vs. null model (train win rate)
    ll_fitted = -log_loss(y_test, y_prob, normalize=False, labels=[0, 1])
    ll_null = -log_loss(
        y_test, np.full(len(y_test), y_train.mean()), normalize=False, labels=[0, 1]
    )

    mean_coefs, std_errors = bootstrap_coefficients(X_train, y_train)
    vif = (
        [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
        if X.shape[1] > 1
        else [np.nan]
    )
    coefficients = pd.DataFrame(
        {
            "Odds ratio": np.exp(model.coef_[0]),
            "Coefficient": model.coef_[0],
            "Mean coefficient": mean_coefs,
            "Standard error": std_errors,
            "P-value": 2 * (1 - norm.cdf(np.abs(model.coef_[0] / std_errors))),
            "VIF": vif,
        },
        index=X.columns,
    )
    return {
        "coefficients": coefficients,
        "class_report": pd.DataFrame(
            classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        ).T,
        "conf_matrix": conf_matrix,
        "roc": roc,
        "auc": auc,
        "accuracy": accuracy_score(y_test, y_pred),
        "mcfadden_r2": 1 - ll_fitted / ll_null,
    }


st.title("Analytics")

with st.expander("Show me a thorough explanation of logistic regression"):
    st.markdown(EXPLANATION)

name, tag = selected_player()
features = st.multiselect(
    "Variables", DEFAULT_FEATURES + EXTRA_FEATURES, default=DEFAULT_FEATURES
)
if not features:
    st.info("Select at least one variable.")
    st.stop()

data = load_data(name, tag, tuple(features))
if data["win"].value_counts().min() < 5 or len(data["win"].unique()) < 2:
    st.warning("Not enough wins and losses to fit a model for this player.")
    st.stop()

with st.spinner("Fitting model..."):
    result = run_regression(data)

main, side = st.columns([3, 1])

with main:
    st.plotly_chart(result["conf_matrix"], use_container_width=True)
    st.subheader("Classification report")
    st.dataframe(result["class_report"].round(2), use_container_width=True)
    st.subheader("Coefficients")
    st.dataframe(result["coefficients"].round(2), use_container_width=True)

with side:
    st.metric("Accuracy", f"{result['accuracy']:.0%}")
    st.metric("McFadden R²", f"{result['mcfadden_r2']:.2f}")
    st.metric("AUC score", f"{result['auc']:.2f}")
    st.plotly_chart(result["roc"], use_container_width=True)