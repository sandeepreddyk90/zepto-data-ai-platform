# Titanic modeling: held-out results

Train balance: {0: 439, 1: 272}; test balance: {0: 110, 1: 68}. Stratification keeps the observed class shares (about 38.2% survived) close in both splits. All numeric median imputation, categorical mode imputation/one-hot encoding, and numeric standardization are fitted inside each training pipeline; test data is transform-only.

## Classification metrics (positive class: survived)

| model               |   accuracy |   precision |   recall |     f1 |    auc |
|:--------------------|-----------:|------------:|---------:|-------:|-------:|
| Logistic Regression |     0.809  |      0.7833 |   0.6912 | 0.7344 | 0.861  |
| Decision Tree       |     0.809  |      0.8148 |   0.6471 | 0.7213 | 0.856  |
| Random Forest       |     0.8146 |      0.807  |   0.6765 | 0.736  | 0.8337 |

Confusion matrices (rows = actual, columns = predicted):
- Logistic Regression: [[97, 13], [21, 47]]
- Decision Tree: [[100, 10], [24, 44]]
- Random Forest: [[99, 11], [22, 46]]

ROC curves, confusion matrices, and the labeled decision tree appear in `charts/`.

## Imbalance strategies (same held-out split)

| variant               |   precision |   recall |     f1 |
|:----------------------|------------:|---------:|-------:|
| baseline              |      0.7833 |   0.6912 | 0.7344 |
| class_weight=balanced |      0.7183 |   0.75   | 0.7338 |
| SMOTE (training only) |      0.7353 |   0.7353 | 0.7353 |

On held-out F1, **SMOTE (training only)** performed best (0.735); compare its precision (0.735) and recall (0.735) before choosing a threshold. SMOTE is placed inside an imbalanced-learn pipeline and is used only when `fit` is called on training rows; it never resamples the test set.

## Tuning and artifact

Random Forest three-fold GridSearchCV best: `{'model__max_depth': 10, 'model__max_features': 0.8, 'model__n_estimators': 200}`; training out-of-bag score: **0.8326**; held-out F1: **0.7879**. OOB is an internal training diagnostic, distinct from held-out evaluation.
Saved complete fitted preprocessing-plus-estimator pipeline: `best_pipeline.joblib` (**Tuned Random Forest**). Reloaded with `joblib.load` and reproduced predictions for five raw, unprocessed held-out input rows: **True**.

## Regression metrics (fare in GBP)

| Model | MAE | RMSE | R² | Adjusted R² |
|---|---:|---:|---:|---:|
| Linear Regression | 21.100 | 41.702 | 0.3482 | 0.3173 |

Residual spread (standard deviation) is 9.89 in the low fitted-fare third and 69.43 in the high third. The spread increases with fitted fare, consistent with heteroscedasticity; see `charts/fare_residuals.png` for the residual pattern. Adjusted R² uses 8 effective predictors after accounting for redundant one-hot indicators.

## Final recommendation

### Combined model comparison (separate metric groups)

| Model               | Classification accuracy   | Classification precision   | Classification recall   | Classification F1   | Classification AUC   | Regression MAE (GBP)   | Regression RMSE (GBP)   | Regression R²   | Regression adjusted R²   |
|:--------------------|:--------------------------|:---------------------------|:------------------------|:--------------------|:---------------------|:-----------------------|:------------------------|:----------------|:-------------------------|
| Logistic Regression | 0.8090                    | 0.7833                     | 0.6912                  | 0.7344              | 0.8610               | —                      | —                       | —               | —                        |
| Decision Tree       | 0.8090                    | 0.8148                     | 0.6471                  | 0.7213              | 0.8560               | —                      | —                       | —               | —                        |
| Random Forest       | 0.8146                    | 0.8070                     | 0.6765                  | 0.7360              | 0.8337               | —                      | —                       | —               | —                        |
| Linear Regression   | —                         | —                          | —                       | —                   | —                    | 21.100                 | 41.702                  | 0.3482          | 0.3173                   |

The classification and regression groups use different targets and scales; blank cells are inapplicable, not missing evaluations.

Deploy **Tuned Random Forest** as the candidate selected by held-out F1 (0.788), using AUC (0.831) as a tie-breaker. Its precision is 0.812 and recall is 0.765 on the stratified test set. The untuned classifier comparison above is on the same held-out rows, while the tuned forest's parameters came only from training cross-validation. This is a teaching benchmark; validate on fresh operational data and tune the decision threshold before real deployment. The regression MAE/RMSE (GBP) and R² scores answer a different prediction question and cannot be ranked against classification scores.
