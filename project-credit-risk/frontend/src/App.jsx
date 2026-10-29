import React, { useState } from 'react';
import axios from 'axios';
import { CreditCard, ShieldAlert } from 'lucide-react';
import MultiStepForm from './components/MultiStepForm';
import DecisionCard from './components/DecisionCard';
import ShapChart from './components/ShapChart';

const API_BASE = "http://localhost:8000";

export default function App() {
  const [predictionResult, setPredictionResult] = useState(null);
  const [explainData, setExplainData] = useState(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleEvaluate = async (formData) => {
    setIsPredicting(true);
    setErrorMsg(null);
    setPredictionResult(null);
    setExplainData(null);

    try {
      const predRes = await axios.post(`${API_BASE}/api/v1/predict`, formData);
      setPredictionResult(predRes.data);
      setIsPredicting(false);

      setIsExplaining(true);
      const explainRes = await axios.get(`${API_BASE}/api/v1/explain/${predRes.data.prediction_id}`);
      setExplainData(explainRes.data);
    } catch (err) {
      console.error("Evaluation error:", err);
      setErrorMsg("Unable to connect to the underwriting server. Please try again.");
    } finally {
      setIsPredicting(false);
      setIsExplaining(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col justify-between">
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CreditCard className="w-5 h-5 text-blue-600" />
            <h1 className="text-lg font-semibold text-slate-900">
              Equitable Credit Risk Engine
            </h1>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <span className="hidden sm:inline">Internal Decision Dashboard</span>
            <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center text-xs border border-blue-200 text-blue-700 font-medium">
              UW
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-8 flex-1 w-full">
        {errorMsg && (
          <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 text-rose-500 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="max-w-3xl mx-auto w-full space-y-8 transition-all duration-500">
          <MultiStepForm isLoading={isPredicting} onSubmit={handleEvaluate} />

          {(predictionResult || isPredicting || explainData) && (
            <div className="space-y-6 animate-fadeIn pt-6 border-t border-slate-200">
              {predictionResult && <DecisionCard result={predictionResult} />}
              <ShapChart explainData={explainData} isLoading={isExplaining} />
            </div>
          )}
        </div>
      </main>

      <footer className="py-6 text-center text-xs text-slate-500 border-t border-slate-200 bg-white">
        &copy; {new Date().getFullYear()} Underwriting Operations. Confidential & Proprietary.
      </footer>
    </div>
  );
}
