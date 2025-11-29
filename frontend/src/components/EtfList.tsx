import { useMemo } from "react";
import { useDashboardData } from "../context/DataContext";

const EtfList = () => {
  const { etfs } = useDashboardData();

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(value);
  };

  const rows = useMemo(
    () =>
      etfs.map((etf) => {
        const changeClass = etf.priceChange >= 0 ? "positive" : "negative";
        const changeSymbol = etf.priceChange >= 0 ? "+" : "";

        return (
          <tr key={etf.ticker}>
            <td className="ticker">{etf.ticker}</td>
            <td className="name-kr">{etf.nameKr}</td>
            <td className="price">{formatCurrency(etf.price)}</td>
            <td className={`change ${changeClass}`}>
              <div className="change-value">
                {changeSymbol}
                {formatCurrency(etf.priceChange)}
              </div>
              <div className="change-percent">
                ({changeSymbol}
                {etf.priceChangePercent.toFixed(2)}%)
              </div>
            </td>
            <td className="dividend">
              {(etf.dividendYield * 100).toFixed(2)}%
            </td>
            <td className="last-dividend">
              {formatDate(etf.lastDividendDate)}
            </td>
          </tr>
        );
      }),
    [etfs]
  );

  return (
    <article className="card etf-list-card">
      <h2>전체 ETF 목록</h2>
      <div className="table-container">
        <table className="etf-table">
          <thead>
            <tr>
              <th>티커</th>
              <th>한글명</th>
              <th>현재가격</th>
              <th>등락</th>
              <th>배당율</th>
              <th>마지막 배당일</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </article>
  );
};

export default EtfList;
