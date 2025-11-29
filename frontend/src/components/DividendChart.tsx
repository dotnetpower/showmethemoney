import { useMemo } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import { DividendHistory } from "../services/etfApi";

interface DividendChartProps {
  dividendHistory: DividendHistory[] | null;
  ticker: string;
}

const DividendChart = ({ dividendHistory, ticker }: DividendChartProps) => {
  const chartData = useMemo(() => {
    if (!dividendHistory || dividendHistory.length === 0) {
      return [];
    }

    return dividendHistory
      .sort((a, b) => new Date(a.ex_date).getTime() - new Date(b.ex_date).getTime())
      .map((item) => ({
        date: new Date(item.ex_date).toLocaleDateString("ko-KR", {
          year: "2-digit",
          month: "short",
        }),
        amount: parseFloat(item.amount),
        fullDate: item.ex_date,
      }));
  }, [dividendHistory]);

  if (!chartData.length) {
    return (
      <div className="dividend-chart-empty">
        <p>배당 이력이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="dividend-chart-container">
      <h3 className="chart-title">{ticker} 배당 추이</h3>
      <div style={{ width: "100%", height: 200 }}>
        <ResponsiveContainer>
          <LineChart
            data={chartData}
            margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11 }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11 }}
              tickLine={false}
              tickFormatter={(value) => `$${value.toFixed(2)}`}
            />
            <Tooltip
              formatter={(value: number) => [`$${value.toFixed(4)}`, "배당금"]}
              labelFormatter={(label) => `배당락일: ${label}`}
              contentStyle={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border-color)",
                borderRadius: "8px",
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="amount"
              name="배당금"
              stroke="#10b981"
              strokeWidth={2}
              dot={{ fill: "#10b981", strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: "#10b981", strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DividendChart;
