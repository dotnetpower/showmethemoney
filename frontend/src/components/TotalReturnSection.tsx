import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";
import { useDashboardData } from "../context/DataContext";

const TotalReturnSection = () => {
  const { totalReturnSeries } = useDashboardData();

  return (
    <article className="card">
      <h2>Total Return ETF</h2>
      <div style={{ width: "100%", height: 240 }}>
        <ResponsiveContainer>
          <LineChart
            data={totalReturnSeries}
            margin={{ top: 16, right: 24, left: 0, bottom: 0 }}
          >
            <XAxis dataKey="date" />
            <YAxis domain={[0, "auto"]} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
};

export default TotalReturnSection;
