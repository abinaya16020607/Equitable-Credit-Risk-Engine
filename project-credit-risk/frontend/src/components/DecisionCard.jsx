import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

export default function DecisionCard({ result }) {
  if (!result) return null;

  const {
    prediction,
    probability,
    recommendation,
    risk_level,
    hard_override,
    override_reason,
    limit_capped,
    threshold_applied,
    prediction_id,
    applicant_id,
    timestamp
  } = result;

  const isApproved = prediction === 0;
  const defaultPercentage = (probability * 100).toFixed(1);
  const safePercentage = ((1 - probability) * 100).toFixed(1);
  const cutoffPercentage = (threshold_applied ? threshold_applied * 100 : 35.0).toFixed(1);

  return (
    <div className="space-y-4">
      {/* Warning Banners */}
      {hard_override && (
        <div className="p-3.5 rounded border border-rose-200 bg-rose-50 text-rose-800 text-xs flex items-start gap-3">
          <XCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block text-rose-900">POLICY OVERRIDE APPLIED</span>
            <p className="text-rose-700 mt-0.5">
              {override_reason || "Automated underwriting rules bypassed due to historical 60+ day delinquencies."}
            </p>
          </div>
        </div>
      )}

      {limit_capped && (
        <div className="p-3.5 rounded border border-amber-200 bg-amber-50 text-amber-800 text-xs flex items-start gap-3">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block text-amber-900">CREDIT LIMIT ADJUSTED</span>
            <p className="text-amber-700 mt-0.5">
              Requested limit exceeded institutional maximum (1.5x annual salary) and was automatically adjusted.
            </p>
          </div>
        </div>
      )}

      {/* Main Decision Container */}
      <div className="bg-white rounded-lg p-6 border border-slate-200 shadow-sm space-y-5">
        {/* Status Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-200 gap-3">
          <div className="flex items-center gap-3">
            {isApproved ? (
              <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0" />
            ) : (
              <XCircle className="w-6 h-6 text-rose-600 shrink-0" />
            )}
            <div>
              <span className="text-[11px] uppercase tracking-wider text-slate-500 block font-medium">
                Underwriting Determination
              </span>
              <h3 className="text-lg font-bold text-slate-900">
                {isApproved ? "Application Approved" : "Application Denied"}
              </h3>
            </div>
          </div>

          <div>
            <span
              className={`px-2.5 py-1 rounded text-xs font-medium border ${
                isApproved
                  ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                  : "bg-rose-50 border-rose-200 text-rose-800"
              }`}
            >
              {risk_level || (isApproved ? "Low Risk" : "High Risk")}
            </span>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-3.5 rounded border border-slate-200 bg-slate-50">
            <span className="text-xs text-slate-500 block mb-1 font-medium">Calculated Default Risk</span>
            <span className={`text-xl font-bold font-mono ${isApproved ? "text-emerald-700" : "text-rose-700"}`}>
              {defaultPercentage}%
            </span>
          </div>

          <div className="p-3.5 rounded border border-slate-200 bg-slate-50">
            <span className="text-xs text-slate-500 block mb-1 font-medium">Approval Confidence</span>
            <span className="text-xl font-bold font-mono text-slate-800">
              {safePercentage}%
            </span>
          </div>

          <div className="p-3.5 rounded border border-slate-200 bg-slate-50">
            <span className="text-xs text-slate-500 block mb-1 font-medium">Risk Policy Threshold</span>
            <span className="text-xl font-bold font-mono text-slate-800">
              {cutoffPercentage}%
            </span>
          </div>
        </div>

        {/* Flat Risk Meter */}
        <div className="space-y-1.5 pt-1">
          <div className="flex justify-between text-xs text-slate-500">
            <span>Risk Score: {defaultPercentage}%</span>
            <span>Policy Cutoff: {cutoffPercentage}%</span>
          </div>
          <div className="w-full h-2 rounded bg-slate-100 border border-slate-200 overflow-hidden relative">
            <div
              className={`h-full transition-all duration-500 ${isApproved ? "bg-emerald-600" : "bg-rose-600"}`}
              style={{ width: `${Math.min(100, Math.max(2, defaultPercentage))}%` }}
            />
          </div>
        </div>

        {/* Audit Details */}
        <div className="pt-4 border-t border-slate-200 flex flex-wrap items-center justify-between text-xs text-slate-500 font-mono gap-2">
          <span>Application ID: {applicant_id}</span>
          <span>Decision ID: {prediction_id}</span>
          <span>Timestamp: {new Date(timestamp).toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
}
