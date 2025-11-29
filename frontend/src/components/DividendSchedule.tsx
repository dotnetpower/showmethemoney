import { useState } from "react";
import { useDashboardData } from "../context/DataContext";

type ViewMode = "weekly" | "monthly";

// 상수 정의
const DEFAULT_COLOR = "#6264A7";
const CHIP_OPACITY = "20";

// 요일에 따른 색상 지정 (Teams 스타일)
const dayColors: Record<string, string> = {
  월: "#6264A7", // Teams Purple
  화: "#ED4A1C", // Orange
  수: "#F2C811", // Yellow
  목: "#107C41", // Green
  금: "#00B294", // Teal
  토: "#0078D4", // Blue
  일: "#D83B01", // Red-Orange
};

// 월별 색상
const monthColors: Record<string, string> = {
  "1월": "#6264A7",
  "2월": "#ED4A1C",
  "3월": "#F2C811",
  "4월": "#107C41",
  "5월": "#00B294",
  "6월": "#0078D4",
  "7월": "#D83B01",
  "8월": "#8764B8",
  "9월": "#E3008C",
  "10월": "#57A300",
  "11월": "#FF8C00",
  "12월": "#00BCF2",
};

const DividendSchedule = () => {
  const { dividendByWeekday, dividendByMonth } = useDashboardData();
  const [viewMode, setViewMode] = useState<ViewMode>("weekly");

  return (
    <div className="dividend-schedule-container">
      {/* 탭 네비게이션 */}
      <div className="schedule-tabs">
        <button
          className={`schedule-tab ${viewMode === "weekly" ? "active" : ""}`}
          onClick={() => setViewMode("weekly")}
        >
          요일별
        </button>
        <button
          className={`schedule-tab ${viewMode === "monthly" ? "active" : ""}`}
          onClick={() => setViewMode("monthly")}
        >
          월별
        </button>
      </div>

      {/* 타임라인 뷰 */}
      <div className="schedule-timeline">
        {viewMode === "weekly" ? (
          <div className="timeline-list">
            {dividendByWeekday.map((item, index) => (
              <div key={item.day} className="timeline-item">
                {/* 타임라인 라인 */}
                <div className="timeline-line">
                  <div
                    className="timeline-dot"
                    style={{ backgroundColor: dayColors[item.day] || DEFAULT_COLOR }}
                  />
                  {index < dividendByWeekday.length - 1 && (
                    <div className="timeline-connector" />
                  )}
                </div>

                {/* 일정 카드 */}
                <div className="timeline-content">
                  <div
                    className="schedule-card"
                    style={{
                      borderLeftColor: dayColors[item.day] || DEFAULT_COLOR,
                    }}
                  >
                    <div className="schedule-card-header">
                      <span className="schedule-day">{item.day}요일</span>
                      <span className="schedule-count">
                        {item.symbols.length}종목
                      </span>
                    </div>
                    <div className="schedule-card-body">
                      <div className="symbol-chips">
                        {item.symbols.map((symbol) => (
                          <span
                            key={symbol}
                            className="symbol-chip"
                            style={{
                              backgroundColor: `${dayColors[item.day] || DEFAULT_COLOR}${CHIP_OPACITY}`,
                              color: dayColors[item.day] || DEFAULT_COLOR,
                            }}
                          >
                            {symbol}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="timeline-list">
            {dividendByMonth.map((item, index) => (
              <div key={item.month} className="timeline-item">
                {/* 타임라인 라인 */}
                <div className="timeline-line">
                  <div
                    className="timeline-dot"
                    style={{
                      backgroundColor: monthColors[item.month] || DEFAULT_COLOR,
                    }}
                  />
                  {index < dividendByMonth.length - 1 && (
                    <div className="timeline-connector" />
                  )}
                </div>

                {/* 일정 카드 */}
                <div className="timeline-content">
                  <div
                    className="schedule-card"
                    style={{
                      borderLeftColor: monthColors[item.month] || DEFAULT_COLOR,
                    }}
                  >
                    <div className="schedule-card-header">
                      <span className="schedule-day">{item.month}</span>
                      <span className="schedule-count">
                        {item.symbols.length}종목
                      </span>
                    </div>
                    <div className="schedule-card-body">
                      <div className="symbol-chips">
                        {item.symbols.map((symbol) => (
                          <span
                            key={symbol}
                            className="symbol-chip"
                            style={{
                              backgroundColor: `${monthColors[item.month] || DEFAULT_COLOR}${CHIP_OPACITY}`,
                              color: monthColors[item.month] || DEFAULT_COLOR,
                            }}
                          >
                            {symbol}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 범례 */}
      <div className="schedule-legend">
        <span className="legend-title">배당 지급 예정</span>
        <span className="legend-info">💰 총 {viewMode === "weekly"
          ? dividendByWeekday.reduce((acc, item) => acc + item.symbols.length, 0)
          : dividendByMonth.reduce((acc, item) => acc + item.symbols.length, 0)
        }개 종목</span>
      </div>
    </div>
  );
};

export default DividendSchedule;
