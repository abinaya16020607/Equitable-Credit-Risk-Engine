import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

# Crucial Windows stability settings for OpenBLAS / NumPy
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
import shap

def run_pipeline():
    print("=" * 70)
    print("  EQUITABLE CREDIT RISK ENGINE: MACHINE LEARNING TRAINING PIPELINE")
    print("  (Engineered Financial Ratios + Balanced Calibrated Random Forest)")
    print("=" * 70)

    # 1. Determine dataset path
    csv_paths = [
        os.path.join(os.path.dirname(__file__), "credit_card_clients_salary.csv"),
        os.path.join(os.getcwd(), "credit_card_clients_salary.csv"),
        "credit_card_clients_salary.csv"
    ]
    csv_file = next((p for p in csv_paths if os.path.exists(p)), None)
    if not csv_file:
        raise FileNotFoundError("credit_card_clients_salary.csv could not be found.")

    print(f"[1/6] Loading dataset from: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"      Initial dataset dimensions: {df.shape[0]} rows, {df.shape[1]} columns")

    # Drop ID column if present
    if "ID" in df.columns:
        df = df.drop(columns=["ID"])
        print("      Dropped 'ID' column to prevent mathematical distortion.")

    target_col = "default.payment.next.month"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")

    # 1b. Feature Engineering: Compute Financial Ratios (Prevents Model Memorization)
    limit_safe = np.where(df["LIMIT_BAL"] == 0, 1.0, df["LIMIT_BAL"])
    df["UTILIZATION_RATIO"] = df["BILL_AMT1"] / limit_safe
    df["INCOME_TO_LIMIT"] = df["SALARY"] / limit_safe
    print("      [Feature Engineering] Created 'UTILIZATION_RATIO' (BILL_AMT1 / LIMIT_BAL)")
    print("      [Feature Engineering] Created 'INCOME_TO_LIMIT' (SALARY / LIMIT_BAL)")

    X = df.drop(columns=[target_col])
    y = df[target_col]
    print(f"      Target distribution: Safe (0) = {(y == 0).sum()}, Default (1) = {(y == 1).sum()}")

    # 2. Define Features Precision including Engineered Financial Ratios
    continuous_features = [
        "LIMIT_BAL", "AGE", "SALARY",
        "UTILIZATION_RATIO", "INCOME_TO_LIMIT",
        "BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6",
        "PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6"
    ]

    nominal_features = ["SEX", "MARRIAGE"]

    # Exact repayment features skipping PAY_1 as specified in the syllabus
    ordinal_features = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]

    all_expected_features = continuous_features + nominal_features + ordinal_features
    X = X[all_expected_features]
    print(f"[2/6] Feature schema verified ({len(all_expected_features)} total input features):")
    print(f"      - Continuous ({len(continuous_features)}): {continuous_features[:5]}... + {len(continuous_features)-5} more")
    print(f"      - Nominal ({len(nominal_features)}): {nominal_features}")
    print(f"      - Ordinal Repayment ({len(ordinal_features)}): {ordinal_features}")

    # 3. Categorical Encoding & Feature Scaling via ColumnTransformer
    print("[3/6] Building ColumnTransformer...")
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), continuous_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), nominal_features),
            ("ord", "passthrough", ordinal_features)
        ],
        remainder="drop"
    )

    # Stratified Train/Test Split (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Fit preprocessor on training data
    preprocessor.fit(X_train)
    X_train_trans = preprocessor.transform(X_train)
    X_test_trans = preprocessor.transform(X_test)

    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_feature_names = list(cat_encoder.get_feature_names_out(nominal_features))
    transformed_feature_names = continuous_features + cat_feature_names + ordinal_features

    # 4. Train Models
    print("[4/6] Training academic syllabus models with calibration & balanced weights...")
    telemetry = {}

    # 4a. Logistic Regression (Linear Baseline + CalibratedClassifierCV)
    print("      -> Training Model 1: Calibrated Logistic Regression (class_weight='balanced', cv=5)...")
    base_lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    lr = CalibratedClassifierCV(estimator=base_lr, cv=5)
    lr.fit(X_train_trans, y_train)
    y_prob_lr = lr.predict_proba(X_test_trans)[:, 1]
    y_pred_lr = (y_prob_lr >= 0.21).astype(int)

    telemetry["logistic_regression"] = {
        "model_name": "Logistic Regression (Balanced & Calibrated)",
        "accuracy": round(float(accuracy_score(y_test, y_pred_lr)), 4),
        "precision": round(float(precision_score(y_test, y_pred_lr, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred_lr, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred_lr, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob_lr)), 4),
        "type": "Linear Baseline (Calibrated)"
    }

    # 4b. Multi-Layer Perceptron (Neural Network / Deep Learning)
    print("      -> Training Model 2: Multi-Layer Perceptron (MLPClassifier)...")
    mlp = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
    mlp.fit(X_train_trans, y_train)
    y_prob_mlp = mlp.predict_proba(X_test_trans)[:, 1]
    y_pred_mlp = (y_prob_mlp >= 0.21).astype(int)

    telemetry["mlp_classifier"] = {
        "model_name": "Multi-Layer Perceptron (Neural Network)",
        "accuracy": round(float(accuracy_score(y_test, y_pred_mlp)), 4),
        "precision": round(float(precision_score(y_test, y_pred_mlp, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred_mlp, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred_mlp, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob_mlp)), 4),
        "type": "Neural Network"
    }

    # 4c. Random Forest Classifier: class_weight=None + CalibratedClassifierCV(cv=5)
    # class_weight=None prevents artificial probability inflation while calibration ensures realistic probabilities
    print("      -> Training Model 3: Calibrated Random Forest (100 Trees, class_weight=None, cv=5)...")
    base_rf = RandomForestClassifier(n_estimators=100, class_weight=None, random_state=42, n_jobs=1)
    rf = CalibratedClassifierCV(estimator=base_rf, cv=5)
    rf.fit(X_train_trans, y_train)
    y_prob_rf = rf.predict_proba(X_test_trans)[:, 1]
    y_pred_rf = (y_prob_rf >= 0.21).astype(int)

    telemetry["random_forest"] = {
        "model_name": "Random Forest (Calibrated)",
        "accuracy": round(float(accuracy_score(y_test, y_pred_rf)), 4),
        "precision": round(float(precision_score(y_test, y_pred_rf, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred_rf, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred_rf, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob_rf)), 4),
        "type": "Ensemble Production Model (Calibrated)"
    }

    # Production pipeline wrapping preprocessor and calibrated classifier
    full_rf_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", rf)
    ])

    print("\n" + "=" * 70)
    print("  ACADEMIC EVALUATION BENCHMARK RESULTS")
    print("=" * 70)
    print(f"{'Model':<40} | {'Accuracy':<9} | {'Precision':<9} | {'Recall':<9} | {'F1':<9} | {'ROC-AUC':<9}")
    print("-" * 93)
    for key, metrics in telemetry.items():
        print(f"{metrics['model_name']:<40} | {metrics['accuracy']:<9.4f} | {metrics['precision']:<9.4f} | {metrics['recall']:<9.4f} | {metrics['f1_score']:<9.4f} | {metrics['roc_auc']:<9.4f}")
    print("=" * 70)

    # 5. Fit SHAP TreeExplainer to the underlying Random Forest tree estimator
    print("[5/6] Fitting SHAP TreeExplainer to Random Forest tree estimator...")
    rf_tree_estimator = rf.calibrated_classifiers_[0].estimator
    background_sample = X_train_trans[:100]
    explainer = shap.TreeExplainer(rf_tree_estimator, data=background_sample, feature_perturbation="interventional")

    # 6. Export production artifacts
    ml_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.abspath(os.path.join(ml_dir, "..", "backend"))
    backend_models_dir = os.path.join(backend_dir, "models")
    os.makedirs(backend_models_dir, exist_ok=True)

    for d in [ml_dir, backend_models_dir]:
        joblib.dump(full_rf_pipeline, os.path.join(d, "credit_rf_model.pkl"))
        joblib.dump(preprocessor, os.path.join(d, "preprocessor.pkl"))
        joblib.dump(explainer, os.path.join(d, "credit_explainer.pkl"))
        joblib.dump(transformed_feature_names, os.path.join(d, "feature_names.pkl"))
        with open(os.path.join(d, "model_telemetry.json"), "w") as f:
            json.dump(telemetry, f, indent=2)

    print("=" * 70)
    print("  CALIBRATED TRAINING PIPELINE COMPLETE & READY FOR PRODUCTION!")
    print("=" * 70)

if __name__ == "__main__":
    run_pipeline()
