import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine
} from 'recharts';
import { BarChart3 } from 'lucide-react';

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const isRisk = data.shap_value > 0;
    return (
      <div className="bg-white border border-slate-200 p-2.5 rounded shadow-md text-xs max-w-xs text-slate-800">
        <p className="font-semibold text-slate-900 mb-1">{data.label}</p>
        <div className="flex items-center justify-between gap-4 py-1 border-t border-slate-100 text-slate-600">
          <span>Relative Impact:</span>
          <span className={`font-mono font-bold ${isRisk ? 'text-rose-600' : 'text-blue-600'}`}>
            {data.shap_value > 0 ? `+${(data.shap_value * 100).toFixed(1)}%` : `${(data.shap_value * 100).toFixed(1)}%`}
          </span>
        </div>
      </div>
    );
  }
  return null;
};

export default function ShapChart({ explainData, isLoading }) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg p-6 border border-slate-200 shadow-sm flex flex-col items-center justify-center min-h-[260px]">
        <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-xs text-slate-500 font-medium">Calculating risk factor contributions...</p>
      </div>
    );
  }

  if (!explainData || !explainData.top_features || explainData.top_features.length === 0) {
    return null;
  }

  const chartData = explainData.top_features.map((item) => ({
    ...item,
    abs_shap: Math.abs(item.shap_value),
    display_label: item.label.length > 24 ? item.label.substring(0, 22) + "..." : item.label,
  }));

  return (
    <div className="bg-white rounded-lg p-6 border border-slate-200 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-200 gap-2">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            <h3 className="text-sm font-semibold text-slate-900">
              Risk Factor Breakdown
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Relative contribution of financial metrics to the credit evaluation.
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-rose-600" />
            <span className="text-slate-600 font-medium">Increases Risk (+)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-blue-600" />
            <span className="text-slate-600 font-medium">Reduces Risk (-)</span>
          </div>
        </div>
      </div>

      {/* Summary Narrative */}
      {explainData.summary && (
        <div className="p-3.5 rounded border border-slate-200 bg-slate-50 text-xs text-slate-700 leading-relaxed">
          {explainData.summary}
        </div>
      )}

      {/* Horizontal Bar Chart */}
      <div className="w-full h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 10, right: 20, left: 130, bottom: 10 }}
          >
            <XAxis
              type="number"
              stroke="#64748b"
              fontSize={11}
              tickFormatter={(v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`}
            />
            <YAxis
              type="category"
              dataKey="display_label"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              width={130}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine x={0} stroke="#cbd5e1" strokeWidth={1} />
            <Bar dataKey="shap_value" radius={[2, 2, 2, 2]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.shap_value > 0 ? '#dc2626' : '#2563eb'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
