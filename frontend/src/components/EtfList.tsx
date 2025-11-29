import { useState, useMemo, useEffect, useRef } from "react";
import { getAllETFs, ETF } from "../services/etfApi";

type SortField =
  | "ticker"
  | "fund_name"
  | "nav_amount"
  | "expense_ratio"
  | "ytd_return"
  | "distribution_yield"
  | "sector"
  | "theme";
type SortDirection = "asc" | "desc";

const EtfList = () => {
  const [etfs, setEtfs] = useState<ETF[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState<SortField>("ticker");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [displayCount, setDisplayCount] = useState(50);
  const [sectorFilter, setSectorFilter] = useState<string>("");
  const [themeFilter, setThemeFilter] = useState<string>("");
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement | null>(null);

  // ETF 데이터 로드
  useEffect(() => {
    const loadETFs = async () => {
      try {
        setLoading(true);
        const data = await getAllETFs();
        setEtfs(data);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "ETF 데이터를 불러오는데 실패했습니다."
        );
      } finally {
        setLoading(false);
      }
    };

    loadETFs();
  }, []);

  // 고유 섹터 및 테마 목록 추출
  const { uniqueSectors, uniqueThemes } = useMemo(() => {
    const sectors = new Set<string>();
    const themes = new Set<string>();
    etfs.forEach((etf) => {
      if (etf.sector) sectors.add(etf.sector);
      if (etf.theme) themes.add(etf.theme);
    });
    return {
      uniqueSectors: Array.from(sectors).sort(),
      uniqueThemes: Array.from(themes).sort(),
    };
  }, [etfs]);

  // 검색 및 필터링
  const filtered = useMemo(() => {
    if (!searchTerm) return etfs;

    const lowerSearch = searchTerm.toLowerCase();
    return etfs.filter(
      (etf) =>
        (etf.ticker?.toLowerCase() || "").includes(lowerSearch) ||
        (etf.fund_name?.toLowerCase() || "").includes(lowerSearch) ||
        (etf.asset_class?.toLowerCase() || "").includes(lowerSearch)
    );
  }, [etfs, searchTerm]);

  // 정렬
  const filteredAndSorted = useMemo(() => {
    const sorted = [...filtered].sort((a, b) => {
      let aValue: string | number | null = a[sortField as keyof ETF] as string | null;
      let bValue: string | number | null = b[sortField as keyof ETF] as string | null;

      // null/undefined 값 처리 (== null은 null과 undefined 둘 다 체크)
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return 1;
      if (bValue == null) return -1;

      // 숫자 필드는 문자열을 숫자로 변환
      if (
        [
          "nav_amount",
          "expense_ratio",
          "ytd_return",
          "distribution_yield",
        ].includes(sortField)
      ) {
        aValue = parseFloat(aValue);
        bValue = parseFloat(bValue);
        // NaN 처리
        if (isNaN(aValue) && isNaN(bValue)) return 0;
        if (isNaN(aValue)) return 1;
        if (isNaN(bValue)) return -1;
      }

      if (aValue < bValue) return sortDirection === "asc" ? -1 : 1;
      if (aValue > bValue) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [filtered, sortField, sortDirection]);

  // 표시할 데이터
  const displayedEtfs = useMemo(() => {
    return filteredAndSorted.slice(0, displayCount);
  }, [filteredAndSorted, displayCount]);

  // 무한 스크롤 구현
  useEffect(() => {
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (
          entries[0].isIntersecting &&
          displayCount < filteredAndSorted.length
        ) {
          setDisplayCount((prev) => prev + 50);
        }
      },
      { threshold: 0.1 }
    );

    observerRef.current = observer;

    if (loadMoreRef.current) {
      observer.observe(loadMoreRef.current);
    }

    return () => {
      observer.disconnect();
    };
  }, [displayCount, filteredAndSorted.length]);

  // 정렬 핸들러
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  // 포맷 함수들
  const formatCurrency = (value: string | null) => {
    if (!value) return "N/A";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(parseFloat(value));
  };

  const formatPercent = (value: string | null) => {
    if (!value) return "N/A";
    const num = parseFloat(value);
    return `${num.toFixed(2)}%`;
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "N/A";
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });
    } catch {
      return "N/A";
    }
  };

  const formatFrequency = (frequency: string | null | undefined) => {
    if (!frequency) return "알 수 없음";
    const frequencyMap: { [key: string]: string } = {
      Weekly: "주배당",
      Monthly: "월배당",
      Quarterly: "분기배당",
      "Semi-Annual": "반기배당",
      Annual: "연배당",
      Variable: "가변",
      None: "무배당",
      Unknown: "알 수 없음",
    };
    return frequencyMap[frequency] || frequency;
  };

  const getSortIndicator = (field: SortField) => {
    if (sortField !== field) return "";
    return sortDirection === "asc" ? " ▲" : " ▼";
  };

  // 투자자 평가 렌더링
  const renderRating = (etf: ETF) => {
    if (!etf.ratings || etf.ratings.length === 0) return "N/A";
    const rating = etf.ratings[0];
    if (rating.rating) return rating.rating;
    if (rating.score) return `${rating.score}점`;
    return "N/A";
  };

  if (loading) {
    return (
      <article className="card etf-list-card">
        <div className="loading-container">
          <p>ETF 데이터를 로딩중입니다...</p>
        </div>
      </article>
    );
  }

  if (error) {
    return (
      <article className="card etf-list-card">
        <div className="error-container">
          <p className="error-message">오류: {error}</p>
        </div>
      </article>
    );
  }

  return (
    <article className="card etf-list-card">
      <h2>전체 ETF 목록</h2>

      {/* 검색 및 필터 바 */}
      <div className="search-container">
        <input
          type="text"
          placeholder="티커, 펀드명, 자산군, 섹터, 테마로 검색..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
        
        {/* 필터 영역 */}
        <div className="filter-container">
          <select
            value={sectorFilter}
            onChange={(e) => setSectorFilter(e.target.value)}
            className="filter-select"
            aria-label="섹터 필터"
          >
            <option value="">모든 섹터</option>
            {uniqueSectors.map((sector) => (
              <option key={sector} value={sector}>
                {sector}
              </option>
            ))}
          </select>
          
          <select
            value={themeFilter}
            onChange={(e) => setThemeFilter(e.target.value)}
            className="filter-select"
            aria-label="테마 필터"
          >
            <option value="">모든 테마</option>
            {uniqueThemes.map((theme) => (
              <option key={theme} value={theme}>
                {theme}
              </option>
            ))}
          </select>
          
          {(sectorFilter || themeFilter) && (
            <button
              onClick={() => {
                setSectorFilter("");
                setThemeFilter("");
              }}
              className="filter-reset-btn"
            >
              필터 초기화
            </button>
          )}
        </div>
        
        <div className="search-info">
          전체 {etfs.length}개 중 {filteredAndSorted.length}개 표시 (현재{" "}
          {displayedEtfs.length}개 로드됨)
        </div>
      </div>

      {/* ETF 테이블 */}
      <div className="table-container">
        <table className="etf-table">
          <thead>
            <tr>
              <th onClick={() => handleSort("ticker")} className="sortable">
                티커{getSortIndicator("ticker")}
              </th>
              <th onClick={() => handleSort("fund_name")} className="sortable">
                펀드명{getSortIndicator("fund_name")}
              </th>
              <th onClick={() => handleSort("nav_amount")} className="sortable">
                NAV{getSortIndicator("nav_amount")}
              </th>
              <th
                onClick={() => handleSort("expense_ratio")}
                className="sortable"
              >
                운용보수{getSortIndicator("expense_ratio")}
              </th>
              <th onClick={() => handleSort("ytd_return")} className="sortable">
                YTD 수익률{getSortIndicator("ytd_return")}
              </th>
              <th
                onClick={() => handleSort("distribution_yield")}
                className="sortable"
              >
                배당수익률{getSortIndicator("distribution_yield")}
              </th>
              <th>배당주기</th>
              <th onClick={() => handleSort("sector")} className="sortable">
                섹터{getSortIndicator("sector")}
              </th>
              <th onClick={() => handleSort("theme")} className="sortable">
                테마{getSortIndicator("theme")}
              </th>
              <th>평가</th>
            </tr>
          </thead>
          <tbody>
            {displayedEtfs.map((etf, index) => (
              <tr key={`etf-${index}`}>
                <td className="ticker">{etf.ticker || "-"}</td>
                <td className="fund-name">{etf.fund_name || "-"}</td>
                <td className="nav">{formatCurrency(etf.nav_amount)}</td>
                <td className="expense-ratio">
                  {formatPercent(etf.expense_ratio)}
                </td>
                <td
                  className={`ytd-return ${
                    etf.ytd_return && parseFloat(etf.ytd_return) >= 0
                      ? "positive"
                      : "negative"
                  }`}
                >
                  {formatPercent(etf.ytd_return)}
                </td>
                <td className="distribution-yield">
                  {formatPercent(etf.distribution_yield)}
                </td>
                <td className="distribution-frequency">
                  {formatFrequency(etf.distribution_frequency)}
                </td>
                <td className="nav-as-of">{formatDate(etf.nav_as_of)}</td>
                <td className="asset-class">{etf.asset_class || "-"}</td>
                <td className="region">{etf.region || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 무한 스크롤 트리거 */}
      {displayCount < filteredAndSorted.length && (
        <div ref={loadMoreRef} className="load-more-trigger">
          <p>더 많은 ETF 로딩중...</p>
        </div>
      )}

      {displayCount >= filteredAndSorted.length &&
        filteredAndSorted.length > 0 && (
          <div className="end-of-list">
            <p>모든 ETF를 표시했습니다.</p>
          </div>
        )}
    </article>
  );
};

export default EtfList;
