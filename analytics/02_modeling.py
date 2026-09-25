"""Continue from the single cleaned Titanic CSV; fit all transforms on train only."""
from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, confusion_matrix,
                             f1_score, mean_absolute_error, mean_squared_error,
                             precision_score, r2_score, recall_score, roc_auc_score, RocCurveDisplay)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree

ROOT = Path(__file__).resolve().parent
CHARTS = ROOT / "charts"; CHARTS.mkdir(exist_ok=True)
NUMERIC = ["pclass", "age", "sibsp", "parch", "fare"]
CATEGORICAL = ["sex", "embarked"]


def preprocessing(numeric=NUMERIC, categorical=CATEGORICAL):
    return ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), categorical),
    ], sparse_threshold=0)


def classifier(algorithm):
    return Pipeline([("preprocess", preprocessing()), ("model", algorithm)])


def metrics(model, x, y):
    pred = model.predict(x)
    prob = model.predict_proba(x)[:, 1]
    return dict(accuracy=accuracy_score(y, pred), precision=precision_score(y, pred, zero_division=0),
                recall=recall_score(y, pred), f1=f1_score(y, pred), auc=roc_auc_score(y, prob)), pred


def main():
    df = pd.read_csv(ROOT / "titanic_clean.csv")
    X, y = df[NUMERIC + CATEGORICAL], df["survived"]
    # Do this before any fitting, including imputation. Stratification preserves
    # the observed approximately 62/38 nonsurvivor/survivor split in both sets.
    xt, xv, yt, yv = train_test_split(X, y, test_size=.2, random_state=42, stratify=y)
    print("train/test class balance", yt.value_counts().to_dict(), yv.value_counts().to_dict())
    models = {
        "Logistic Regression": classifier(LogisticRegression(max_iter=1000, random_state=42)),
        "Decision Tree": classifier(DecisionTreeClassifier(max_depth=4, random_state=42)),
        "Random Forest": classifier(RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42, n_jobs=-1)),
    }
    rows, predictions = [], {}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig2, ax2 = plt.subplots(figsize=(7, 5))
    for ax, (name, model) in zip(axes, models.items()):
        model.fit(xt, yt)
        scores, pred = metrics(model, xv, yv)
        rows.append({"model": name, **scores})
        predictions[name] = pred
        ConfusionMatrixDisplay.from_predictions(yv, pred, ax=ax, colorbar=False)
        ax.set_title(name)
        RocCurveDisplay.from_estimator(model, xv, yv, ax=ax2, name=name)
    fig.tight_layout(); fig.savefig(CHARTS / "confusion_matrices.png", dpi=130); plt.close(fig)
    fig2.tight_layout(); fig2.savefig(CHARTS / "roc_curves.png", dpi=130); plt.close(fig2)
    tree = models["Decision Tree"]
    plt.figure(figsize=(20, 11))
    plot_tree(tree.named_steps["model"], feature_names=tree.named_steps["preprocess"].get_feature_names_out(),
              class_names=["not survived", "survived"], filled=True, rounded=True, fontsize=7)
    plt.tight_layout(); plt.savefig(CHARTS / "decision_tree.png", dpi=130); plt.close()
    comparison = pd.DataFrame(rows).set_index("model")

    variants = {
        "baseline": classifier(LogisticRegression(max_iter=1000, random_state=42)),
        "class_weight=balanced": classifier(LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
        "SMOTE (training only)": ImbPipeline([("preprocess", preprocessing()), ("smote", SMOTE(random_state=42)), ("model", LogisticRegression(max_iter=1000, random_state=42))]),
    }
    imbalance = []
    for name, model in variants.items():
        model.fit(xt, yt)
        score, _ = metrics(model, xv, yv)
        imbalance.append({"variant": name, **score})
    imbalance = pd.DataFrame(imbalance).set_index("variant")

    grid = GridSearchCV(classifier(RandomForestClassifier(oob_score=True, bootstrap=True, random_state=42, n_jobs=-1)),
                        {"model__n_estimators": [100, 200], "model__max_depth": [5, 10, None], "model__max_features": ["sqrt", .8]},
                        scoring="f1", cv=3, n_jobs=-1)
    grid.fit(xt, yt)  # CV fits preprocessing separately inside each training fold.
    tuned = grid.best_estimator_
    tuned_score, _ = metrics(tuned, xv, yv)
    candidates = {**models, "Tuned Random Forest": tuned}
    candidate_scores = {r["model"]: r for r in rows}
    candidate_scores["Tuned Random Forest"] = tuned_score
    winner = max(candidates, key=lambda name: (candidate_scores[name]["f1"], candidate_scores[name]["auc"]))
    artifact = ROOT / "best_pipeline.joblib"
    joblib.dump(candidates[winner], artifact)
    reloaded = joblib.load(artifact)
    assert np.array_equal(reloaded.predict(xv.head(5)), candidates[winner].predict(xv.head(5)))

    # Fare is the regression target, excluded from predictors; class/sex/age/
    # family/embarkation/survival are available fields, with no 'alive' leakage.
    reg_num = ["survived", "pclass", "age", "sibsp", "parch"]
    reg_cols = reg_num + CATEGORICAL
    rx, ry = df[reg_cols], df["fare"]
    rxt, rxv, ryt, ryv = train_test_split(rx, ry, test_size=.2, random_state=42)
    reg = Pipeline([("preprocess", preprocessing(reg_num, CATEGORICAL)), ("model", LinearRegression())])
    reg.fit(rxt, ryt)
    fitted = reg.predict(rxv); residual = ryv.to_numpy() - fitted
    p = reg.named_steps["preprocess"].transform(rxv).shape[1] - len(CATEGORICAL)  # one redundant indicator per categorical field with an intercept.
    n = len(ryv); r2 = r2_score(ryv, fitted)
    adjusted = 1 - (1-r2)*(n-1)/(n-p-1)
    mae, rmse = mean_absolute_error(ryv, fitted), np.sqrt(mean_squared_error(ryv, fitted))
    plt.scatter(fitted, residual, alpha=.55); plt.axhline(0, color="black")
    plt.xlabel("Fitted fare"); plt.ylabel("Residual (actual − fitted)")
    plt.tight_layout(); plt.savefig(CHARTS / "fare_residuals.png", dpi=130); plt.close()
    # Quantify changing spread across fitted-fare bands; still inspect the plot.
    low, high = np.quantile(fitted, [.33, .67])
    low_sd = residual[fitted <= low].std(ddof=1); high_sd = residual[fitted >= high].std(ddof=1)

    best_imbalance = imbalance["f1"].idxmax()
    grouped_rows = []
    for name, values in comparison.iterrows():
        grouped_rows.append({"Model": name, "Classification accuracy": f"{values.accuracy:.4f}",
                             "Classification precision": f"{values.precision:.4f}",
                             "Classification recall": f"{values.recall:.4f}",
                             "Classification F1": f"{values.f1:.4f}",
                             "Classification AUC": f"{values.auc:.4f}",
                             "Regression MAE (GBP)": "—", "Regression RMSE (GBP)": "—",
                             "Regression R²": "—", "Regression adjusted R²": "—"})
    grouped_rows.append({"Model": "Linear Regression", "Classification accuracy": "—",
                         "Classification precision": "—", "Classification recall": "—",
                         "Classification F1": "—", "Classification AUC": "—",
                         "Regression MAE (GBP)": f"{mae:.3f}", "Regression RMSE (GBP)": f"{rmse:.3f}",
                         "Regression R²": f"{r2:.4f}", "Regression adjusted R²": f"{adjusted:.4f}"})
    lines = ["# Titanic modeling: held-out results", "", f"Train balance: {yt.value_counts().sort_index().to_dict()}; test balance: {yv.value_counts().sort_index().to_dict()}. Stratification keeps the observed class shares (about {100*y.mean():.1f}% survived) close in both splits. All numeric median imputation, categorical mode imputation/one-hot encoding, and numeric standardization are fitted inside each training pipeline; test data is transform-only.", "", "## Classification metrics (positive class: survived)", "", comparison.round(4).to_markdown(), "", "Confusion matrices (rows = actual, columns = predicted):"]
    for name, pred in predictions.items(): lines.append(f"- {name}: {confusion_matrix(yv, pred).tolist()}")
    lines += ["", "ROC curves, confusion matrices, and the labeled decision tree appear in `charts/`.", "", "## Imbalance strategies (same held-out split)", "", imbalance[["precision", "recall", "f1"]].round(4).to_markdown(), "", f"On held-out F1, **{best_imbalance}** performed best ({imbalance.loc[best_imbalance, 'f1']:.3f}); compare its precision ({imbalance.loc[best_imbalance, 'precision']:.3f}) and recall ({imbalance.loc[best_imbalance, 'recall']:.3f}) before choosing a threshold. SMOTE is placed inside an imbalanced-learn pipeline and is used only when `fit` is called on training rows; it never resamples the test set.", "", "## Tuning and artifact", "", f"Random Forest three-fold GridSearchCV best: `{grid.best_params_}`; training out-of-bag score: **{tuned.named_steps['model'].oob_score_:.4f}**; held-out F1: **{tuned_score['f1']:.4f}**. OOB is an internal training diagnostic, distinct from held-out evaluation.", f"Saved complete fitted preprocessing-plus-estimator pipeline: `best_pipeline.joblib` (**{winner}**). Reloaded with `joblib.load` and reproduced predictions for five raw, unprocessed held-out input rows: **True**.", "", "## Regression metrics (fare in GBP)", "", "| Model | MAE | RMSE | R² | Adjusted R² |", "|---|---:|---:|---:|---:|", f"| Linear Regression | {mae:.3f} | {rmse:.3f} | {r2:.4f} | {adjusted:.4f} |", "", f"Residual spread (standard deviation) is {low_sd:.2f} in the low fitted-fare third and {high_sd:.2f} in the high third. {'The spread increases with fitted fare, consistent with heteroscedasticity' if high_sd > 1.25*low_sd else 'These thirds do not alone show a strong widening, so a clear heteroscedasticity claim is not supported'}; see `charts/fare_residuals.png` for the residual pattern. Adjusted R² uses {p} effective predictors after accounting for redundant one-hot indicators.", "", "## Final recommendation", ""]
    ws = candidate_scores[winner]
    lines += ["### Combined model comparison (separate metric groups)", "", pd.DataFrame(grouped_rows).to_markdown(index=False), "", "The classification and regression groups use different targets and scales; blank cells are inapplicable, not missing evaluations.", "", f"Deploy **{winner}** as the candidate selected by held-out F1 ({ws['f1']:.3f}), using AUC ({ws['auc']:.3f}) as a tie-breaker. Its precision is {ws['precision']:.3f} and recall is {ws['recall']:.3f} on the stratified test set. The untuned classifier comparison above is on the same held-out rows, while the tuned forest's parameters came only from training cross-validation. This is a teaching benchmark; validate on fresh operational data and tune the decision threshold before real deployment. The regression MAE/RMSE (GBP) and R² scores answer a different prediction question and cannot be ranked against classification scores."]
    (ROOT / "model_results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__": main()
