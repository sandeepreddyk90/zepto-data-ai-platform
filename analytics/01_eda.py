"""One raw Seaborn load, committed offline fallback, and reproducible EDA."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent
CHARTS = ROOT / "charts"
CHARTS.mkdir(exist_ok=True)


def load() -> pd.DataFrame:
    path = ROOT / "titanic.csv"
    if path.exists() and "--refresh" not in sys.argv:
        print("Reading previously saved raw Seaborn CSV")
        return pd.read_csv(path)
    df = sns.load_dataset("titanic")  # The only loader call anywhere in this module.
    df.to_csv(path, index=False)  # Required exact offline snapshot, saved immediately after loading.
    return df


def save(name: str) -> None:
    plt.tight_layout()
    plt.savefig(CHARTS / f"{name}.png", dpi=130)
    plt.close()


def main() -> None:
    df = load()
    print("shape:", df.shape)
    df.info()
    print(df.describe(include="all").to_string())
    missing = (100 * df.isna().mean()).loc[lambda s: s > 0]
    print("Missing percentages:\n", missing.to_string())
    # <5% rows dropped (embarked and equivalent embark_town); >30% deck dropped.
    # Age (5–30%) is imputed into an EDA-only copy. The model learns its own
    # training-fold median so no full-data statistic can leak into evaluation.
    clean = df.dropna(subset=["embarked", "embark_town"]).drop(columns=["deck"]).copy()
    clean.to_csv(ROOT / "titanic_clean.csv", index=False)
    eda = clean.copy()
    age_median = eda["age"].median()
    eda["age"] = eda["age"].fillna(age_median)
    lines = ["# Titanic EDA: measured results", "", f"Raw shape: **{df.shape[0]} × {df.shape[1]}**; survival balance: **{df['survived'].value_counts().sort_index().to_dict()}**.", "", "## Missing values and cleaning", "", "| Column | Missing | Decision |", "|---|---:|---|"]
    for col, val in missing.items():
        strategy = ("Drop affected rows (<5% missing)" if col in ("embarked", "embark_town") else "Impute age with median for EDA; training-fold imputer for models (5–30%)" if col == "age" else "Drop deck column (>30% missing; a dominant missing category would be weak evidence)")
        lines.append(f"| {col} | {val:.2f}% | {strategy} |")
    lines += ["", f"After dropping the same two rows missing embarkation, {len(clean)} rows remain. EDA age median: {age_median:.2f}. `titanic_clean.csv` retains age nulls intentionally, so training estimates the model's imputer only after the split.", "", "## Univariate analysis", ""]
    for col in ("age", "fare"):
        fig, ax = plt.subplots(1, 2, figsize=(10, 4))
        sns.histplot(eda[col], ax=ax[0], bins=30)
        sns.boxplot(x=eda[col], ax=ax[1])
        fig.suptitle(f"{col}: distribution and outliers")
        save(f"{col}_hist_box")
        q1, q3 = eda[col].quantile([.25, .75]); iqr = q3 - q1
        n = ((eda[col] < q1 - 1.5 * iqr) | (eda[col] > q3 + 1.5 * iqr)).sum()
        lines.append(f"- `{col}`: {n} outliers under [Q1 − 1.5×IQR, Q3 + 1.5×IQR] ({q1:.2f}, {q3:.2f}; IQR {iqr:.2f}). See `charts/{col}_hist_box.png`.")
    mean, med, mode = eda.fare.mean(), eda.fare.median(), eda.fare.mode().iloc[0]
    lines += [f"- Fare mean **{mean:.2f}**, median **{med:.2f}**, mode **{mode:.2f}**. Mean > median > mode indicates a right-skewed distribution with a high-fare tail.", "", "## Bivariate rates (boolean masks)", ""]
    for label, cols in (("sex", ["sex"]), ("pclass", ["pclass"]), ("sex × pclass", ["sex", "pclass"])):
        lines.append(f"### {label}")
        for key in eda.groupby(cols).size().index:
            values = key if isinstance(key, tuple) else (key,)
            mask = pd.Series(True, index=eda.index)
            for c, v in zip(cols, values): mask = mask & (eda[c] == v)
            lines.append(f"- {', '.join(map(str, values))}: {eda.loc[mask, 'survived'].mean():.3f} ({mask.sum()} passengers)")
        lines.append("")
    cols = ["survived", "pclass", "age", "sibsp", "parch", "fare"]
    corr = eda[cols].corr()
    sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1)
    save("six_variable_heatmap")
    pairs = [(abs(corr.loc[a,b]), a,b,corr.loc[a,b]) for i,a in enumerate(cols) for b in cols[i+1:]]
    pairs.sort(reverse=True)
    lines += ["## Exactly six numeric columns", "", "The heatmap uses `survived`, `pclass`, `age`, `sibsp`, `parch`, `fare`; derived flags `adult_male` and `alone` are excluded."]
    for _,a,b,c in pairs[:2]: lines.append(f"- `{a}` vs `{b}`: r = **{c:.3f}**; {'positive' if c > 0 else 'negative'} association (ranked by absolute off-diagonal correlation). Correlation is descriptive, not causal.")
    lines += ["", "## Four multivariate charts and interpretations", ""]
    sns.barplot(data=eda, x="pclass", y="survived", hue="sex", errorbar=None); save("01_survival_class_sex")
    lines += ["### 1. Survival by class and sex", "", "The sex gap appears within each passenger class, so the overall difference is not only a shift in class composition. Class also changes survival rates within sex groups. These associations do not establish the reason for an individual's outcome.", ""]
    sns.boxplot(data=eda, x="survived", y="age", hue="sex"); save("02_age_sex_survival")
    lines += ["### 2. Age by outcome and sex", "", "The overlapping age distributions show that age alone separates survivors poorly. Sex helps expose different outcome patterns at similar ages. Missing ages were median-filled for this exploratory view only.", ""]
    sns.boxplot(data=eda, x="pclass", y="fare", hue="survived", showfliers=False); save("03_fare_class_survival")
    lines += ["### 3. Fare by class and outcome", "", "Fare differs markedly across classes, so a fare–survival association may partly reflect class. Within-class boxes still vary by outcome, but their overlap discourages a simple fare cutoff. Extreme fares are hidden in this plot for legibility, not removed from the dataset.", ""]
    sns.barplot(data=eda, x="pclass", y="survived", hue="embarked", errorbar=None); save("04_class_embarked_survival")
    lines += ["### 4. Survival by class and embarkation", "", "Rates vary across both boarding point and class, suggesting that a one-variable explanation is incomplete. Some combinations have fewer passengers and therefore less stable observed rates. This view motivates evaluating several features together.", ""]
    z = eda[["age", "fare"]].apply(lambda s: (s - s.mean()) / s.std(ddof=0))
    lines += ["## Exploratory z-score check (not reused by modeling)", "", "| Feature | Raw mean | Raw std (ddof=0) | Z mean | Z std (ddof=0) |", "|---|---:|---:|---:|---:|"]
    for col in ("age", "fare"):
        lines.append(f"| {col} | {eda[col].mean():.3f} | {eda[col].std(ddof=0):.3f} | {z[col].mean():.6f} | {z[col].std(ddof=0):.6f} |")
    lines += ["", "This full-data z-score is a visualization sanity check only. The modeling pipeline separately fits a `StandardScaler` on training folds."]
    (ROOT / "eda_results.md").write_text("\n".join(lines) + "\n")
    print("Saved", ROOT / "eda_results.md")


if __name__ == "__main__": main()
