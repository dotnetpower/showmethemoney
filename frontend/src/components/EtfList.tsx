import { useMemo } from "react";
import { useDashboardData } from "../context/DataContext";

const EtfList = () => {
  const { etfs } = useDashboardData();
  const rows = useMemo(
    () =>
      etfs.map((etf) => (
        <tr key={etf.ticker}>
          <td>{etf.ticker}</td>
          <td>{etf.price.toLocaleString()}</td>
          <td>{(etf.dividendYield * 100).toFixed(2)}%</td>
          <td>{etf.marketCap.toLocaleString()}</td>
        </tr>
      )),
    [etfs]
  );

  return (
    <article className="card">
      <h2>전체 ETF 목록</h2>
      <table>
        <thead>
          <tr>
            <th>티커</th>
            <th>가격</th>
            <th>배당율</th>
            <th>시가총액</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </article>
  );
};

export default EtfList;
