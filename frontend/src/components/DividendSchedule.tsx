import { useDashboardData } from "../context/DataContext";

const DividendSchedule = () => {
  const { dividendByWeekday, dividendByMonth } = useDashboardData();

  return (
    <article className="card">
      <h2>배당 일정</h2>
      <div className="two-column">
        <section>
          <h3>요일별</h3>
          <ul>
            {dividendByWeekday.map((item) => (
              <li key={item.day}>
                <strong>{item.day}</strong>: {item.symbols.join(", ")}
              </li>
            ))}
          </ul>
        </section>
        <section>
          <h3>월별</h3>
          <ul>
            {dividendByMonth.map((item) => (
              <li key={item.month}>
                <strong>{item.month}</strong>: {item.symbols.join(", ")}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </article>
  );
};

export default DividendSchedule;
