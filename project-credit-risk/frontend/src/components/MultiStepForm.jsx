import React, { useState } from 'react';
import { CreditCard, ChevronRight, ChevronLeft } from 'lucide-react';

const PRESETS = {
  prime: {
    label: "Test Profile A",
    data: {
      SALARY: 175000,
      LIMIT_BAL: 262500,
      AGE: 40,
      SEX: 1, // Male
      MARRIAGE: 1, // Married
      PAY_0: -1, // On time
      PAY_2: -1,
      PAY_3: -1,
      PAY_4: 0,
      PAY_5: 0,
      PAY_6: 0,
      BILL_AMT1: 18500,
      BILL_AMT2: 17200,
      BILL_AMT3: 15400,
      BILL_AMT4: 12100,
      BILL_AMT5: 9800,
      BILL_AMT6: 6400,
      PAY_AMT1: 18500,
      PAY_AMT2: 17200,
      PAY_AMT3: 15400,
      PAY_AMT4: 12100,
      PAY_AMT5: 9800,
      PAY_AMT6: 6400,
    }
  },
  defaulter: {
    label: "Test Profile B",
    data: {
      SALARY: 32000,
      LIMIT_BAL: 48000,
      AGE: 24,
      SEX: 2, // Female
      MARRIAGE: 2, // Single
      PAY_0: 2, // Delay 2 months
      PAY_2: 2, // Delay 2 months
      PAY_3: 1, // Delay 1 month
      PAY_4: 2, // Delay 2 months
      PAY_5: 0,
      PAY_6: 0,
      BILL_AMT1: 78500,
      BILL_AMT2: 77200,
      BILL_AMT3: 75000,
      BILL_AMT4: 73000,
      BILL_AMT5: 69000,
      BILL_AMT6: 65000,
      PAY_AMT1: 1000,
      PAY_AMT2: 500,
      PAY_AMT3: 800,
      PAY_AMT4: 0,
      PAY_AMT5: 500,
      PAY_AMT6: 0,
    }
  }
};

const PAY_OPTIONS = [
  { value: -2, label: "-2: No consumption" },
  { value: -1, label: "-1: Paid in full / on time" },
  { value: 0, label: " 0: Revolving credit used" },
  { value: 1, label: " 1: Delay of 1 month" },
  { value: 2, label: " 2: Delay of 2 months" },
  { value: 3, label: " 3: Delay of 3 months" },
  { value: 4, label: " 4: Delay of 4 months" },
  { value: 5, label: " 5: Delay of 5+ months" },
];

export default function MultiStepForm({ onSubmit, isLoading }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState(PRESETS.prime.data);

  const applyPreset = (key) => {
    setFormData({ ...PRESETS[key].data });
  };

  const handleChange = (field, value) => {
    let parsedValue = typeof value === 'string' && !isNaN(Number(value)) && value !== '' ? Number(value) : value;

    // Dynamic Limit Constraint: LIMIT_BAL <= SALARY * 1.5
    if (field === 'LIMIT_BAL' && typeof parsedValue === 'number') {
      const maxAllowedLimit = (Number(formData.SALARY) || 0) * 1.5;
      if (parsedValue > maxAllowedLimit) {
        parsedValue = maxAllowedLimit;
      }
    }

    // Dynamic Repayment Constraint: PAY_AMT <= BILL_AMT
    if (typeof field === 'string' && field.startsWith('PAY_AMT') && typeof parsedValue === 'number') {
      const monthIndex = field.replace('PAY_AMT', '');
      const billKey = `BILL_AMT${monthIndex}`;
      const statementBalance = Number(formData[billKey]) || 0;
      if (parsedValue > statementBalance) {
        parsedValue = statementBalance;
      }
    }

    setFormData(prev => ({
      ...prev,
      [field]: parsedValue
    }));
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    if (step < 4) {
      setStep((s) => Math.min(4, s + 1));
      return;
    }
    onSubmit(formData);
  };

  return (
    <div className="bg-white rounded-lg p-6 border border-slate-200 shadow-sm">
      {/* Header & Testing Presets */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200">
        <div>
          <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-blue-600" />
            Applicant Intake Form
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Please enter the applicant's financial details.
          </p>
        </div>

        {/* Flat Presets */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Presets:</span>
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              applyPreset('prime');
            }}
            className="text-xs px-2.5 py-1.5 rounded border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 font-medium transition-colors"
          >
            Test Profile A
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              applyPreset('defaulter');
            }}
            className="text-xs px-2.5 py-1.5 rounded border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 font-medium transition-colors"
          >
            Test Profile B
          </button>
        </div>
      </div>

      {/* Flat Corporate Tabs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 border-b border-slate-200 my-6">
        {[
          { num: 1, title: "1. Demographics" },
          { num: 2, title: "2. Financials" },
          { num: 3, title: "3. Repayment History" },
          { num: 4, title: "4. Statements & Payments" },
        ].map((s) => (
          <button
            key={s.num}
            type="button"
            onClick={(e) => {
              e.preventDefault();
              setStep(s.num);
            }}
            className={`py-2.5 px-3 text-xs text-center truncate transition-colors ${
              step === s.num
                ? "border-b-2 border-blue-600 text-blue-600 font-semibold bg-blue-50/50"
                : "border-b-2 border-transparent text-slate-500 hover:text-slate-800 font-medium hover:bg-slate-50"
            }`}
          >
            {s.title}
          </button>
        ))}
      </div>

      <form onSubmit={handleFormSubmit}>
        {/* STEP 1: Demographics */}
        {step === 1 && (
          <div className="space-y-4">
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-3">
              Personal Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1.5">Gender</label>
                <select
                  value={formData.SEX}
                  onChange={(e) => handleChange("SEX", Number(e.target.value))}
                  className="w-full bg-white border border-slate-300 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value={1}>1 - Male</option>
                  <option value={2}>2 - Female</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1.5">Marital Status</label>
                <select
                  value={formData.MARRIAGE}
                  onChange={(e) => handleChange("MARRIAGE", Number(e.target.value))}
                  className="w-full bg-white border border-slate-300 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value={1}>1 - Married</option>
                  <option value={2}>2 - Single</option>
                  <option value={3}>3 - Others</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1.5">Age (Years)</label>
                <input
                  type="number"
                  min="18"
                  max="100"
                  value={formData.AGE}
                  onChange={(e) => handleChange("AGE", e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: Financial Metrics */}
        {step === 2 && (
          <div className="space-y-4">
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-3">
              Income & Credit Line
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded border border-slate-200 bg-slate-50">
                <label className="block text-xs font-medium text-slate-700 mb-1 flex items-center justify-between">
                  <span>Annual Income ($)</span>
                  <span className="text-slate-900 font-mono text-sm font-semibold">${Number(formData.SALARY || 0).toLocaleString()}</span>
                </label>
                <input
                  type="number"
                  min="5000"
                  step="1000"
                  value={formData.SALARY}
                  onChange={(e) => handleChange("SALARY", e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g. 150000"
                  required
                />
              </div>

              <div className="p-4 rounded border border-slate-200 bg-slate-50">
                <label className="block text-xs font-medium text-slate-700 mb-1 flex items-center justify-between">
                  <span>Approved Credit Limit ($)</span>
                  <span className="text-slate-900 font-mono text-sm font-semibold">${Number(formData.LIMIT_BAL || 0).toLocaleString()}</span>
                </label>
                <input
                  type="number"
                  min="1000"
                  step="1000"
                  value={formData.LIMIT_BAL}
                  onChange={(e) => handleChange("LIMIT_BAL", e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g. 200000"
                  required
                />
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: Repayment Status */}
        {step === 3 && (
          <div className="space-y-4">
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-3">
              Repayment Timeliness History
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {[
                { key: "PAY_0", label: "Month 1 Status" },
                { key: "PAY_2", label: "Month 2 Status" },
                { key: "PAY_3", label: "Month 3 Status" },
                { key: "PAY_4", label: "Month 4 Status" },
                { key: "PAY_5", label: "Month 5 Status" },
                { key: "PAY_6", label: "Month 6 Status" },
              ].map((item) => (
                <div key={item.key} className="p-3 rounded border border-slate-200 bg-slate-50">
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">{item.label}</label>
                  <select
                    name={item.key}
                    value={formData[item.key]}
                    onChange={(e) => handleChange(item.key, Number(e.target.value))}
                    className="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {PAY_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* STEP 4: Statements & Payments */}
        {step === 4 && (
          <div className="space-y-4">
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-3">
              Monthly Statement Balances & Amounts Paid
            </h3>

            <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
              {[1, 2, 3, 4, 5, 6].map((idx) => {
                const billKey = `BILL_AMT${idx}`;
                const payKey = `PAY_AMT${idx}`;
                return (
                  <div key={idx} className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 rounded border border-slate-200 bg-slate-50">
                    <div>
                      <label className="block text-[11px] font-medium text-slate-700 mb-1 flex justify-between">
                        <span>Month {idx} Balance</span>
                        <span className="text-slate-500 font-mono">${Number(formData[billKey] || 0).toLocaleString()}</span>
                      </label>
                      <input
                        name={billKey}
                        type="number"
                        value={formData[billKey]}
                        onChange={(e) => handleChange(billKey, e.target.value)}
                        className="w-full bg-white border border-slate-300 rounded px-3 py-1.5 text-xs text-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-medium text-slate-700 mb-1 flex justify-between">
                        <span>Month {idx} Paid</span>
                        <span className="text-slate-500 font-mono">${Number(formData[payKey] || 0).toLocaleString()}</span>
                      </label>
                      <input
                        name={payKey}
                        type="number"
                        value={formData[payKey]}
                        onChange={(e) => handleChange(payKey, e.target.value)}
                        className="w-full bg-white border border-slate-300 rounded px-3 py-1.5 text-xs text-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        required
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Footer Navigation Controls */}
        <div className="flex items-center justify-between pt-5 mt-6 border-t border-slate-200">
          <button
            type="button"
            disabled={step === 1}
            onClick={(e) => {
              e.preventDefault();
              setStep((s) => Math.max(1, s - 1));
            }}
            className="px-4 py-2 rounded text-xs font-medium text-slate-700 border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-30 disabled:pointer-events-none transition flex items-center gap-1.5"
          >
            <ChevronLeft className="w-4 h-4" /> Previous
          </button>

          {step < 4 ? (
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                setStep((s) => Math.min(4, s + 1));
              }}
              className="px-5 py-2 rounded text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 transition flex items-center gap-1.5"
            >
              Next Step <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2 rounded text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 transition flex items-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Processing...
                </>
              ) : (
                "Evaluate Applicant"
              )}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
