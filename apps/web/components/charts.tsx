"use client";
import {
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Area,
  Line,
  ComposedChart,
  BarChart,
  Bar,
  ReferenceLine,
  Cell,
} from "recharts";
import { money, month } from "@/lib/api";
import { Row, Analysis } from "@/lib/types";

const axis = {
  tickLine: false,
  axisLine: false,
  tick: { fill: "#93a6b7", fontSize: 11 },
};
export function RevenueChart({ rows }: { rows: Row[] }) {
  return (
    <div
      className="chart-frame"
      role="img"
      aria-label="Monthly revenue compared with target and prior year"
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={rows}
          margin={{ top: 20, right: 15, bottom: 5, left: 5 }}
        >
          <defs>
            <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#65c9bb" stopOpacity={0.16} />
              <stop offset="100%" stopColor="#65c9bb" stopOpacity={0.01} />
            </linearGradient>
          </defs>
          <CartesianGrid
            vertical={false}
            stroke="#283641"
            strokeDasharray="3 3"
          />
          <XAxis dataKey="month" tickFormatter={month} {...axis} dy={10} />
          <YAxis tickFormatter={(v) => money(v)} {...axis} width={67} />
          <Tooltip
            formatter={(v) => money(Number(v), false)}
            labelFormatter={(v) => month(String(v))}
            contentStyle={{
              background: "#15232e",
              color: "#e4edf4",
              border: "1px solid #324654",
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Line
            isAnimationActive={false}
            name="Prior year"
            type="monotone"
            dataKey="prior_year_revenue"
            stroke="#4b6174"
            dot={false}
            strokeWidth={1.5}
          />
          <Line
            isAnimationActive={false}
            name="Target"
            type="monotone"
            dataKey="target"
            stroke="#8297af"
            strokeDasharray="5 5"
            dot={false}
            strokeWidth={1.5}
          />
          <Area
            isAnimationActive={false}
            name="Revenue"
            type="monotone"
            dataKey="revenue"
            stroke="#65c9bb"
            fill="url(#revenueFill)"
            strokeWidth={2.5}
            dot={{ r: 3, fill: "#14212a", strokeWidth: 2 }}
            activeDot={{ r: 5 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
export function GapChart({ rows }: { rows: Row[] }) {
  return (
    <div
      className="chart-frame"
      role="img"
      aria-label="Product revenue gap to target"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={rows}
          layout="vertical"
          margin={{ top: 5, right: 35, bottom: 5, left: 10 }}
        >
          <CartesianGrid horizontal={false} stroke="#283641" />
          <XAxis type="number" tickFormatter={(v) => money(v)} {...axis} />
          <YAxis dataKey="product" type="category" {...axis} width={65} />
          <Tooltip
            contentStyle={{
              background: "#15232e",
              border: "1px solid #344957",
              borderRadius: 6,
              color: "#e4edf4",
            }}
            formatter={(v) => money(Number(v), false)}
            cursor={{ fill: "#1d303c" }}
          />
          <ReferenceLine x={0} stroke="#607382" />
          <Bar
            isAnimationActive={false}
            dataKey="gap"
            name="Gap to target"
            radius={[0, 3, 3, 0]}
            barSize={16}
          >
            {rows.map((r, i) => (
              <Cell key={i} fill={r.gap < 0 ? "#d4a17c" : "#65c9bb"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
export function ForecastChart({ data }: { data: Analysis }) {
  const rows = [
    ...data.history
      .slice(-12)
      .map((r) => ({ month: r.month, revenue: r.revenue })),
    ...data.forecast.map((r) => ({ ...r, band: [r.lower, r.upper] })),
  ];
  return (
    <div
      className="chart-frame tall"
      role="img"
      aria-label="Historical revenue and three-month exploratory forecast"
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={rows}>
          <CartesianGrid vertical={false} stroke="#283641" />
          <XAxis dataKey="month" tickFormatter={month} {...axis} />
          <YAxis tickFormatter={(v) => money(v)} {...axis} width={75} />
          <Tooltip
            contentStyle={{
              background: "#15232e",
              border: "1px solid #344957",
              borderRadius: 6,
              color: "#e4edf4",
            }}
            formatter={(v) => money(Number(v), false)}
          />
          <Area
            isAnimationActive={false}
            dataKey="band"
            name="Exploratory residual band"
            stroke="none"
            fill="#e0b47d"
            fillOpacity={0.15}
          />
          <Line
            isAnimationActive={false}
            dataKey="revenue"
            name="Historical revenue"
            stroke="#65c9bb"
            dot={false}
            strokeWidth={2}
          />
          <Line
            isAnimationActive={false}
            dataKey="forecast"
            name="Forecast"
            stroke="#e0b47d"
            dot={{ r: 4 }}
            strokeWidth={2}
            strokeDasharray="5 4"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
