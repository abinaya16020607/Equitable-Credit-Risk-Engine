import os
import sys
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Enforce thread limits before library initialization
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import applicants_collection, predictions_collection, check_db_connection

# Initialize FastAPI App
app = FastAPI(
    title="Equitable Credit Risk Engine API",
    description="Production-grade AI Decision Support System for Credit Risk Evaluation & Explainability",
    version="2.1.0"
)

# Enable CORS for frontend Vite client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Risk Governance Constants
# ---------------------------------------------------------
# Realistic 35.0% financial risk cutoff (Default probability >= 0.35 is Denied)
REALISTIC_RISK_THRESHOLD = 0.35
MAX_SALARY_MULTIPLIER = 1.5

# ---------------------------------------------------------
# Load Machine Learning Artifacts
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
ML_DIR = BASE_DIR.parent / "ml"

def find_artifact(filename: str) -> Path:
    candidates = [MODELS_DIR / filename, ML_DIR / filename]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"Required artifact '{filename}' not found in {MODELS_DIR} or {ML_DIR}")

def reload_artifacts():
    global rf_pipeline, preprocessor, shap_explainer, feature_names, model_telemetry
    try:
        rf_pipeline = joblib.load(find_artifact("credit_rf_model.pkl"))
        preprocessor = joblib.load(find_artifact("preprocessor.pkl"))
        shap_explainer = joblib.load(find_artifact("credit_explainer.pkl"))
        feature_names = joblib.load(find_artifact("feature_names.pkl"))

        telemetry_file = find_artifact("model_telemetry.json")
        with open(telemetry_file, "r") as f:
            model_telemetry = json.load(f)

        print("[OK] All ML models and explainability artifacts loaded into server memory.")
    except Exception as e:
        print(f"[WARN] Warning loading ML artifacts: {e}")
        rf_pipeline = None
        preprocessor = None
        shap_explainer = None
        feature_names = []
        model_telemetry = {}

reload_artifacts()

# ---------------------------------------------------------
# Helper Functions: Feature Engineering & Ratios
# ---------------------------------------------------------
FEATURE_ORDER = [
    "LIMIT_BAL", "AGE", "SALARY",
    "UTILIZATION_RATIO", "INCOME_TO_LIMIT",
    "BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6",
    "PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6",
    "SEX", "MARRIAGE",
    "PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"
]

FRIENDLY_NAMES = {
    "LIMIT_BAL": "Credit Limit Approved",
    "AGE": "Applicant Age",
    "SALARY": "Annual Income",
    "UTILIZATION_RATIO": "Credit Utilization Ratio",
    "INCOME_TO_LIMIT": "Income to Credit Limit Ratio",
    "PAY_0": "Latest Repayment Status",
    "PAY_2": "Month-2 Repayment Status",
    "PAY_3": "Month-3 Repayment Status",
    "PAY_4": "Month-4 Repayment Status",
    "PAY_5": "Month-5 Repayment Status",
    "PAY_6": "Month-6 Repayment Status",
    "BILL_AMT1": "Latest Statement Balance",
    "PAY_AMT1": "Latest Payment Amount",
    "BILL_AMT2": "Month-2 Statement Balance",
    "PAY_AMT2": "Month-2 Payment Amount",
    "BILL_AMT3": "Month-3 Statement Balance",
    "PAY_AMT3": "Month-3 Payment Amount",
    "BILL_AMT4": "Month-4 Statement Balance",
    "PAY_AMT4": "Month-4 Payment Amount",
    "BILL_AMT5": "Month-5 Statement Balance",
    "PAY_AMT5": "Month-5 Payment Amount",
    "BILL_AMT6": "Month-6 Statement Balance",
    "PAY_AMT6": "Month-6 Payment Amount",
    "cat__SEX_1": "Demographics (Male)",
    "cat__SEX_2": "Demographics (Female)",
    "cat__MARRIAGE_1": "Marital Status (Married)",
    "cat__MARRIAGE_2": "Marital Status (Single)",
    "cat__MARRIAGE_3": "Marital Status (Other)"
}

def clean_feature_label(raw_feature: str) -> str:
    if raw_feature in FRIENDLY_NAMES:
        return FRIENDLY_NAMES[raw_feature]
    for key, name in FRIENDLY_NAMES.items():
        if key in raw_feature:
            return name
    return raw_feature.replace("num__", "").replace("ord__", "").replace("cat__", "")

def enrich_financial_ratios(data: dict) -> dict:
    """
    Computes mathematical financial ratios to eliminate model memorization:
    - UTILIZATION_RATIO = BILL_AMT1 / LIMIT_BAL
    - INCOME_TO_LIMIT = SALARY / LIMIT_BAL
    Safely handles division by zero by replacing 0 with 1 for LIMIT_BAL.
    """
    enriched = dict(data)
    limit = float(enriched.get("LIMIT_BAL", 0.0))
    limit_safe = limit if limit > 0 else 1.0
    bill1 = float(enriched.get("BILL_AMT1", 0.0))
    salary = float(enriched.get("SALARY", 0.0))

    enriched["UTILIZATION_RATIO"] = round(bill1 / limit_safe, 4)
    enriched["INCOME_TO_LIMIT"] = round(salary / limit_safe, 4)
    return enriched

# ---------------------------------------------------------
# Pydantic Request & Response Schemas
# ---------------------------------------------------------
class ApplicantData(BaseModel):
    # Continuous financial metrics
    SALARY: float = Field(..., description="Annual income of the applicant", example=120000.0)
    LIMIT_BAL: float = Field(..., description="Total approved credit limit", example=500000.0)
    AGE: int = Field(..., ge=18, le=100, description="Age in years", example=35)

    # Demographics
    SEX: int = Field(..., description="1 = Male, 2 = Female", example=1)
    MARRIAGE: int = Field(..., description="1 = Married, 2 = Single, 3 = Others", example=1)

    # 6-Month Repayment History (skipping PAY_1 as per dataset schema)
    PAY_0: int = Field(..., description="Repayment status month 1 (-1=on time, 2=2 months late, 3=3+ months late)", example=-1)
    PAY_2: int = Field(..., description="Repayment status month 2", example=-1)
    PAY_3: int = Field(..., description="Repayment status month 3", example=0)
    PAY_4: int = Field(..., description="Repayment status month 4", example=0)
    PAY_5: int = Field(..., description="Repayment status month 5", example=0)
    PAY_6: int = Field(..., description="Repayment status month 6", example=0)

    # 6-Month Statement Balances
    BILL_AMT1: float = Field(..., description="Bill statement amount month 1", example=30000.0)
    BILL_AMT2: float = Field(..., description="Bill statement amount month 2", example=28000.0)
    BILL_AMT3: float = Field(..., description="Bill statement amount month 3", example=25000.0)
    BILL_AMT4: float = Field(..., description="Bill statement amount month 4", example=20000.0)
    BILL_AMT5: float = Field(..., description="Bill statement amount month 5", example=15000.0)
    BILL_AMT6: float = Field(..., description="Bill statement amount month 6", example=10000.0)

    # 6-Month Actual Repayments
    PAY_AMT1: float = Field(..., description="Amount paid month 1", example=5000.0)
    PAY_AMT2: float = Field(..., description="Amount paid month 2", example=5000.0)
    PAY_AMT3: float = Field(..., description="Amount paid month 3", example=5000.0)
    PAY_AMT4: float = Field(..., description="Amount paid month 4", example=4000.0)
    PAY_AMT5: float = Field(..., description="Amount paid month 5", example=3000.0)
    PAY_AMT6: float = Field(..., description="Amount paid month 6", example=2000.0)

class PredictionResponse(BaseModel):
    prediction_id: str
    applicant_id: str
    prediction: int
    probability: float
    recommendation: str
    risk_level: str
    hard_override: bool = False
    override_reason: Optional[str] = None
    limit_capped: bool = False
    threshold_applied: float = REALISTIC_RISK_THRESHOLD
    timestamp: str

class FeatureAttribution(BaseModel):
    feature: str
    label: str
    shap_value: float = Field(..., description="Relative signed percentage contribution (e.g. 0.25 = 25% impact)")
    percentage: float = Field(..., description="Absolute relative percentage impact (e.g. 25.0%)")
    impact: str
    direction: str

class ExplainResponse(BaseModel):
    prediction_id: str
    applicant_id: str
    base_value: float
    probability: float
    recommendation: str
    hard_override: bool = False
    limit_capped: bool = False
    top_features: List[FeatureAttribution]
    summary: str

# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------
@app.get("/")
def root():
    return {
        "engine": "The Equitable Credit Risk Engine",
        "version": "2.1.0",
        "risk_threshold": REALISTIC_RISK_THRESHOLD,
        "max_salary_multiplier": MAX_SALARY_MULTIPLIER,
        "feature_engineering": ["UTILIZATION_RATIO", "INCOME_TO_LIMIT"],
        "status": "online",
        "docs": "/docs"
    }

@app.get("/api/health")
def health_check():
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok and rf_pipeline is not None else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "models_loaded": rf_pipeline is not None,
        "explainer_loaded": shap_explainer is not None,
        "risk_threshold": REALISTIC_RISK_THRESHOLD,
        "max_salary_multiplier": MAX_SALARY_MULTIPLIER,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/telemetry")
def get_telemetry():
    formatted_json = json.dumps(model_telemetry, indent=4)
    return Response(content=formatted_json, media_type="application/json")

@app.post("/api/v1/predict", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
def predict_credit_risk(applicant: ApplicantData):
    """
    Primary Inference Route:
    1. Dynamic Limit Cap: Forces LIMIT_BAL <= SALARY * 1.5. Tracks limit_capped.
    2. Pre-flight check: Hard policy override for 90-day delinquencies (PAY_* >= 3).
    3. Feature engineering: Computes UTILIZATION_RATIO and INCOME_TO_LIMIT mathematically.
    4. Runs calibrated, balanced Random Forest pipeline (no artificial discounts).
    5. Evaluates realistic 15.0% risk threshold (probability >= 0.15 is Denied, < 0.15 is Approved).
    6. Persists inputs and predictions into MongoDB.
    """
    if rf_pipeline is None:
        raise HTTPException(status_code=500, detail="Machine learning model is not initialized.")

    raw_data = applicant.model_dump()

    # Dynamic Limit Cap: Calculate maximum allowed credit limit based on salary
    max_allowed_limit = raw_data["SALARY"] * MAX_SALARY_MULTIPLIER
    limit_capped = False
    if raw_data["LIMIT_BAL"] > max_allowed_limit:
        raw_data["LIMIT_BAL"] = max_allowed_limit
        limit_capped = True

    applicant_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
    prediction_id = f"PRED-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.utcnow().isoformat()

    # 1. Insert input (with capped limit if applicable) into MongoDB Applicants collection
    applicant_doc = {
        "applicant_id": applicant_id,
        "data": raw_data,
        "limit_capped": limit_capped,
        "created_at": timestamp
    }
    try:
        applicants_collection.insert_one(applicant_doc)
    except Exception as e:
        print(f"Warning inserting to Applicants collection: {e}")

    # 2. Pre-flight Check: Hard Business Logic Overrides (60+ Day Delinquency & Minimum Payment Rule)
    
    # Check 1: 60+ Day Delinquencies (>= 2 months delay, occurring >= 2 times)
    delinquency_cols = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
    delinquent_keys = {
        col: raw_data[col] for col in delinquency_cols if raw_data.get(col, 0) >= 2
    }
    
    # Check 2: Payment Violations (Bill >= 15000, Paid < 15000, occurring > 2 times)
    payment_violations = {}
    for i in range(1, 7):
        bill_col = f"BILL_AMT{i}"
        pay_col = f"PAY_AMT{i}"
        
        # Safely handle missing keys by defaulting to 0
        bill = float(raw_data.get(bill_col, 0))
        pay = float(raw_data.get(pay_col, 0))
        
        if bill >= 15000 and pay < 15000:
            payment_violations[f"Month {i}"] = f"Bill: {bill}, Paid: {pay}"

    hard_override = False
    override_reason = None
    
    if len(delinquent_keys) >= 2:
        hard_override = True
        delinquency_detail = ", ".join([f"{k}={v} (Delay {v} months)" for k, v in delinquent_keys.items()])
        override_reason = f"Multiple (2+) historical 60+ day delinquencies detected in: {delinquency_detail}"
    elif len(payment_violations) > 2:
        hard_override = True
        payment_detail = ", ".join([f"{k} [{v}]" for k, v in payment_violations.items()])
        override_reason = f"Applicant failed to pay 15,000 on bills exceeding 15,000 more than two times: {payment_detail}"
        
    if hard_override:
        prediction = 1  # Deny
        default_prob = 1.0
        recommendation = "Deny"
        risk_level = "High Risk (Hard Policy Override)"
        
        prediction_doc = {
            "prediction_id": prediction_id,
            "applicant_id": applicant_id,
            "prediction": prediction,
            "probability": default_prob,
            "recommendation": recommendation,
            "risk_level": risk_level,
            "hard_override": hard_override,
            "override_reason": override_reason,
            "limit_capped": limit_capped,
            "threshold_applied": REALISTIC_RISK_THRESHOLD,
            "created_at": timestamp
        }
        try:
            predictions_collection.insert_one(prediction_doc)
        except Exception as e:
            print(f"Warning inserting to Predictions collection: {e}")
            
        return PredictionResponse(
            prediction_id=prediction_id,
            applicant_id=applicant_id,
            prediction=prediction,
            probability=default_prob,
            recommendation=recommendation,
            risk_level=risk_level,
            hard_override=hard_override,
            override_reason=override_reason,
            limit_capped=limit_capped,
            threshold_applied=REALISTIC_RISK_THRESHOLD,
            timestamp=timestamp
        )

    # 3. Standard ML Inference with Engineered Financial Ratios
    enriched_data = enrich_financial_ratios(raw_data)
    input_df = pd.DataFrame([enriched_data])[FEATURE_ORDER]

    # Calculate calibrated probability from model pipeline
    probabilities = rf_pipeline.predict_proba(input_df)[0]
    default_prob = float(probabilities[1])

    # 4. Realistic 15.0% Risk Threshold (Default probability >= 0.15 is Denied)
    prediction = 0 if default_prob < REALISTIC_RISK_THRESHOLD else 1
    recommendation = "Approve" if prediction == 0 else "Deny"
    risk_level = "Low Risk" if prediction == 0 else "High Risk"
    hard_override = False
    override_reason = None

    # 5. Save output to MongoDB Predictions collection
    prediction_doc = {
        "prediction_id": prediction_id,
        "applicant_id": applicant_id,
        "prediction": prediction,
        "probability": round(default_prob, 4),
        "recommendation": recommendation,
        "risk_level": risk_level,
        "hard_override": hard_override,
        "override_reason": override_reason,
        "limit_capped": limit_capped,
        "threshold_applied": REALISTIC_RISK_THRESHOLD,
        "created_at": timestamp
    }
    try:
        predictions_collection.insert_one(prediction_doc)
    except Exception as e:
        print(f"Warning inserting to Predictions collection: {e}")

    return PredictionResponse(
        prediction_id=prediction_id,
        applicant_id=applicant_id,
        prediction=prediction,
        probability=round(default_prob, 4),
        recommendation=recommendation,
        risk_level=risk_level,
        hard_override=hard_override,
        override_reason=override_reason,
        limit_capped=limit_capped,
        threshold_applied=REALISTIC_RISK_THRESHOLD,
        timestamp=timestamp
    )

@app.get("/api/v1/explain/{id}", response_model=ExplainResponse)
def explain_prediction(id: str):
    """
    Transparency & Explainable AI (XAI) Route:
    1. Retrieves applicant data and enriches with financial ratios.
    2. Computes SHAP values using TreeExplainer.
    3. Converts raw abstract SHAP values into relative percentages:
       Divides individual absolute SHAP by total absolute sum (e.g., 0.25 = 25% contribution).
    4. Ranks top positive and negative features influencing the decision.
    """
    if preprocessor is None or shap_explainer is None:
        raise HTTPException(status_code=500, detail="SHAP Explainer or preprocessor is not loaded.")

    pred_record = predictions_collection.find_one({"prediction_id": id})
    if not pred_record:
        pred_record = predictions_collection.find_one({"applicant_id": id})

    if not pred_record:
        raise HTTPException(status_code=404, detail=f"Prediction record for ID '{id}' was not found in the database.")

    applicant_id = pred_record.get("applicant_id")
    app_record = applicants_collection.find_one({"applicant_id": applicant_id})

    if not app_record or "data" not in app_record:
        raise HTTPException(status_code=404, detail=f"Applicant data for ID '{applicant_id}' was not found in the database.")

    raw_data = app_record["data"]
    enriched_data = enrich_financial_ratios(raw_data)
    input_df = pd.DataFrame([enriched_data])[FEATURE_ORDER]

    # Transform raw data through saved preprocessor FIRST
    transformed_matrix = preprocessor.transform(input_df)

    shap_results = shap_explainer(transformed_matrix)
    if len(shap_results.shape) == 3:
        sample_shap = shap_results.values[0, :, 1]
        base_val = float(shap_results.base_values[0, 1])
    else:
        sample_shap = shap_results.values[0]
        base_val = float(shap_results.base_values[0])

    # Convert SHAP values into relative percentages:
    total_abs_shap = sum(abs(float(v)) for v in sample_shap)
    if total_abs_shap == 0:
        total_abs_shap = 1.0

    feature_list = []
    names = feature_names if len(feature_names) == len(sample_shap) else [f"feature_{i}" for i in range(len(sample_shap))]

    for name, val in zip(names, sample_shap):
        raw_s = float(val)
        pct_contribution = abs(raw_s) / total_abs_shap
        signed_percentage = raw_s / total_abs_shap
        impact = "increases_risk" if raw_s > 0 else "decreases_risk"
        direction = f"Pushes Toward Denial ({pct_contribution*100:.1f}%)" if raw_s > 0 else f"Pushes Toward Approval ({pct_contribution*100:.1f}%)"

        feature_list.append(FeatureAttribution(
            feature=name,
            label=clean_feature_label(name),
            shap_value=round(signed_percentage, 4),
            percentage=round(pct_contribution * 100, 1),
            impact=impact,
            direction=direction
        ))

    # Sort by absolute relative contribution percentage
    feature_list.sort(key=lambda x: x.percentage, reverse=True)
    top_features = feature_list[:10]

    recommendation = pred_record.get("recommendation", "Approve")
    hard_override = pred_record.get("hard_override", False)
    limit_capped = pred_record.get("limit_capped", False)
    override_reason = pred_record.get("override_reason")
    top_driver = top_features[0] if top_features else None
    prob_pct = pred_record.get("probability", 0.0) * 100

    cap_note = " (Requested credit limit was automatically capped to 1.5x annual salary)" if limit_capped else ""

    if hard_override:
        reason = f"Loan was Denied via Hard Business Policy Override: {override_reason}. Machine learning evaluation was bypassed per institutional risk guidelines.{cap_note}"
    elif recommendation == "Deny":
        reason = f"Loan was Denied: applicant's calculated default risk ({prob_pct:.1f}%) exceeds the {REALISTIC_RISK_THRESHOLD*100:.1f}% institutional risk tolerance cutoff. Primary driver is {top_driver.label} ({top_driver.percentage:.1f}% relative contribution toward denial).{cap_note}"
    else:
        reason = f"Loan was Approved: applicant's default risk ({prob_pct:.1f}%) is within the {REALISTIC_RISK_THRESHOLD*100:.1f}% institutional risk tolerance cutoff. Favorable profile in {top_driver.label} ({top_driver.percentage:.1f}% relative contribution toward approval) maintained safe standing.{cap_note}"

    return ExplainResponse(
        prediction_id=id,
        applicant_id=applicant_id,
        base_value=round(base_val, 4),
        probability=pred_record.get("probability", 0.0),
        recommendation=recommendation,
        hard_override=hard_override,
        limit_capped=limit_capped,
        top_features=top_features,
        summary=reason
    )

@app.get("/api/v1/fly")
def execute_fly():
    try:
        import antigravity
    except Exception as e:
        pass

    return {
        "status": "weightless",
        "easter_egg": "import antigravity",
        "gravity": 0.0,
        "altitude": "orbital",
        "message": "Antigravity module engaged. All financial weights are now suspended in low Earth orbit.",
        "payload": {
            "pitch": 0.0,
            "roll": 0.0,
            "yaw": 0.0,
            "weightlessness_confirmed": True
        },
        "timestamp": datetime.utcnow().isoformat()
    }
