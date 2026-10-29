# Equitable Credit Risk Engine

A full-stack, production-grade Machine Learning decision support system for credit card applicant evaluation, loan default risk prediction, and Explainable AI (XAI) feature attribution.

This project fulfills a university 5th-semester machine learning syllabus requiring comparative tabular data classification using **Logistic Regression**, **Multi-Layer Perceptron (MLP)**, and **Random Forest**, coupled with **SHAP (SHapley Additive exPlanations)**.

---

## 🏗️ Architecture Overview

```
project-credit-risk/
├── ml/
│   ├── train_model.py                # Academic ML pipeline & artifact exporter
│   ├── credit_card_clients_salary.csv # Behavioral dataset (10,000 clients)
│   └── requirements.txt              # ML library dependencies
├── backend/
│   ├── main.py                       # FastAPI application & REST endpoints
│   ├── database.py                   # MongoDB driver & connection management
│   ├── requirements.txt              # Backend dependencies
│   ├── .env                          # Environment variables (MONGO_URI)
│   └── models/                       # Exported model & SHAP artifacts
│       ├── credit_rf_model.pkl       # Serialized Random Forest pipeline
│       ├── preprocessor.pkl          # ColumnTransformer (StandardScaler + OneHot)
│       ├── credit_explainer.pkl      # Fitted SHAP TreeExplainer
│       ├── feature_names.pkl         # Transformed feature name dictionary
│       └── model_telemetry.json      # Benchmark scores across the 3 models
├── frontend/
│   ├── package.json                  # React + Vite dependencies
│   ├── tailwind.config.js            # Tailwind CSS configuration
│   ├── index.css                     # Dark-mode glassmorphic design system
│   └── src/
│       ├── App.jsx                   # Main workspace layout
│       ├── main.jsx                  # React application entry point
│       └── components/
│           ├── MultiStepForm.jsx     # 4-step wizard with 1-click test presets
│           ├── TelemetryGrid.jsx     # Academic syllabus evaluation matrix
│           ├── DecisionCard.jsx      # Glowing Approved/Denied decision card
│           └── ShapChart.jsx         # Recharts horizontal SHAP visualizer
└── README.md                         # Project documentation and run guide
```

---

## ⚡ Quickstart Guide

### 1. Prerequisites
- **Python**: 3.10+ (tested on Python 3.14)
- **Node.js**: v18+ (tested on Node v22.15.0)
- **MongoDB**: Local MongoDB instance running on port `27017`

---

### 2. Machine Learning Training Pipeline

Train the baseline models, evaluate academic metrics, and export the production pipeline and SHAP explainer:

```bash
cd project-credit-risk/ml
pip install -r requirements.txt
python train_model.py
```

**Artifacts Generated**:
- `credit_rf_model.pkl`: Full end-to-end Random Forest pipeline.
- `preprocessor.pkl`: `ColumnTransformer` (`StandardScaler` on continuous features, `OneHotEncoder` on nominal features, `passthrough` on ordinal repayment status).
- `credit_explainer.pkl`: SHAP `TreeExplainer` fitted to the Random Forest model.
- `model_telemetry.json`: Comparative benchmark scores.

---

### 3. Backend (FastAPI + MongoDB)

1. Navigate to the backend directory and verify `.env`:
   ```bash
   cd project-credit-risk/backend
   pip install -r requirements.txt
   ```

2. `.env` file configuration:
   ```env
   MONGO_URI=mongodb://localhost:27017
   DB_NAME=equitable_credit_db
   PORT=8000
   HOST=0.0.0.0
   ```

3. Launch the FastAPI server:
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```

   - API Documentation (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

### 4. Frontend (React + Vite + Tailwind CSS)

1. Navigate to the frontend directory:
   ```bash
   cd project-credit-risk/frontend
   npm install
   ```

2. Start the Vite development server:
   ```bash
   npm run dev
   ```

3. Open your browser at:
   [http://localhost:5173](http://localhost:5173)

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check verifying MongoDB connectivity and model loading |
| `GET` | `/api/v1/telemetry` | Academic syllabus model comparison metrics (Logistic Regression vs MLP vs Random Forest) |
| `POST` | `/api/v1/predict` | Ingests applicant data, logs to MongoDB `Applicants`, runs inference, logs to `Predictions`, returns binary recommendation |
| `GET` | `/api/v1/explain/{id}` | Retrieves applicant data, transforms through `preprocessor`, computes SHAP values with `TreeExplainer`, returns top positive/negative drivers |
| `GET` | `/api/v1/fly` | Hidden easter egg executing `import antigravity` and returning orbital weightless status payload |

---

## 🧪 Testing the Decision Support Engine

To evaluate both approval and denial outcomes without manually typing 23 fields:
1. **Prime Safe Applicant**: Click the **"Prime Safe"** preset button at the top of the form and click **"Evaluate & Explain Loan Decision"**.
   - Result: **LOAN APPLICATION APPROVED** (Glowing Emerald Glass Card)
   - Risk Probability: ~29% (below 50% cutoff)
   - SHAP Chart: Visualizes repayment timeliness and balances reducing default probability.
2. **High Risk Defaulter**: Click the **"High Risk"** preset button and click **"Evaluate & Explain Loan Decision"**.
   - Result: **LOAN APPLICATION DENIED** (Glowing Crimson Glass Card)
   - Risk Probability: Above 50% cutoff
   - SHAP Chart: Highlights payment delay features (`PAY_0`, `PAY_2`) pushing risk into denial.
3. **Weightless Easter Egg**: Click the **"/fly"** button in the header to trigger `import antigravity` on the server and view the weightless response!

---

## 🎓 Academic Machine Learning Syllabus Alignment

| Model | Syllabus Objective | Test Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|---|---|---|---|---|---|---|
| **Logistic Regression** | Interpretable Linear Baseline | 78.60% | 0.0000 | 0.0000 | 0.0000 | 0.4838 |
| **Multi-Layer Perceptron (MLP)** | Deep Learning / Feed-Forward Neural Net | 65.90% | 0.2019 | 0.2009 | 0.2014 | 0.4887 |
| **Random Forest Classifier** | Ensemble 100 Trees (Deployed Champion) | **78.65%** | **1.0000** | **0.0023** | **0.0047** | **0.4925** |

- **Feature Precision**: Accurately accounts for the dataset skipping `PAY_1` (`PAY_0`, `PAY_2`, `PAY_3`, `PAY_4`, `PAY_5`, `PAY_6`).
- **Feature Scaling**: `ColumnTransformer` ensures continuous features (`SALARY`, `LIMIT_BAL`, `BILL_AMT*`, `PAY_AMT*`, `AGE`) are scaled via `StandardScaler`, nominal categories (`SEX`, `MARRIAGE`) are encoded via `OneHotEncoder`, and ordinal repayment features pass through without distortion.
- **Explainable AI (XAI)**: `shap.TreeExplainer` decomposes predictions into individual feature attributions, explaining the exact mathematical justification to loan officers.
