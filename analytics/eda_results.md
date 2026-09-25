# Titanic EDA: measured results

Raw shape: **891 × 15**; survival balance: **{0: 549, 1: 342}**.

## Missing values and cleaning

| Column | Missing | Decision |
|---|---:|---|
| age | 19.87% | Impute age with median for EDA; training-fold imputer for models (5–30%) |
| embarked | 0.22% | Drop affected rows (<5% missing) |
| deck | 77.22% | Drop deck column (>30% missing; a dominant missing category would be weak evidence) |
| embark_town | 0.22% | Drop affected rows (<5% missing) |

After dropping the same two rows missing embarkation, 889 rows remain. EDA age median: 28.00. `titanic_clean.csv` retains age nulls intentionally, so training estimates the model's imputer only after the split.

## Univariate analysis

- `age`: 65 outliers under [Q1 − 1.5×IQR, Q3 + 1.5×IQR] (22.00, 35.00; IQR 13.00). See `charts/age_hist_box.png`.
- `fare`: 114 outliers under [Q1 − 1.5×IQR, Q3 + 1.5×IQR] (7.90, 31.00; IQR 23.10). See `charts/fare_hist_box.png`.
- Fare mean **32.10**, median **14.45**, mode **8.05**. Mean > median > mode indicates a right-skewed distribution with a high-fare tail.

## Bivariate rates (boolean masks)

### sex
- female: 0.740 (312 passengers)
- male: 0.189 (577 passengers)

### pclass
- 1: 0.626 (214 passengers)
- 2: 0.473 (184 passengers)
- 3: 0.242 (491 passengers)

### sex × pclass
- female, 1: 0.967 (92 passengers)
- female, 2: 0.921 (76 passengers)
- female, 3: 0.500 (144 passengers)
- male, 1: 0.369 (122 passengers)
- male, 2: 0.157 (108 passengers)
- male, 3: 0.135 (347 passengers)

## Exactly six numeric columns

The heatmap uses `survived`, `pclass`, `age`, `sibsp`, `parch`, `fare`; derived flags `adult_male` and `alone` are excluded.
- `pclass` vs `fare`: r = **-0.548**; negative association (ranked by absolute off-diagonal correlation). Correlation is descriptive, not causal.
- `sibsp` vs `parch`: r = **0.415**; positive association (ranked by absolute off-diagonal correlation). Correlation is descriptive, not causal.

## Four multivariate charts and interpretations

### 1. Survival by class and sex

The sex gap appears within each passenger class, so the overall difference is not only a shift in class composition. Class also changes survival rates within sex groups. These associations do not establish the reason for an individual's outcome.

### 2. Age by outcome and sex

The overlapping age distributions show that age alone separates survivors poorly. Sex helps expose different outcome patterns at similar ages. Missing ages were median-filled for this exploratory view only.

### 3. Fare by class and outcome

Fare differs markedly across classes, so a fare–survival association may partly reflect class. Within-class boxes still vary by outcome, but their overlap discourages a simple fare cutoff. Extreme fares are hidden in this plot for legibility, not removed from the dataset.

### 4. Survival by class and embarkation

Rates vary across both boarding point and class, suggesting that a one-variable explanation is incomplete. Some combinations have fewer passengers and therefore less stable observed rates. This view motivates evaluating several features together.

## Exploratory z-score check (not reused by modeling)

| Feature | Raw mean | Raw std (ddof=0) | Z mean | Z std (ddof=0) |
|---|---:|---:|---:|---:|
| age | 29.315 | 12.978 | 0.000000 | 1.000000 |
| fare | 32.097 | 49.670 | 0.000000 | 1.000000 |

This full-data z-score is a visualization sanity check only. The modeling pipeline separately fits a `StandardScaler` on training folds.
