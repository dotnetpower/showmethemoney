import { useState } from "react";

interface NavigationProps {
  currentView: string;
  onViewChange: (view: string) => void;
}

const Navigation = ({ currentView, onViewChange }: NavigationProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const menuItems = [
    { id: "etf-list", label: "전체 ETF", icon: "📊" },
    { id: "dividend-schedule", label: "배당 일정", icon: "📅" },
    { id: "dividend-simulator", label: "배당 시뮬레이터", icon: "💰" },
    { id: "total-return", label: "Total Return", icon: "📈" },
  ];

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  const handleNavClick = (viewId: string) => {
    onViewChange(viewId);
    setIsOpen(false);
  };

  return (
    <nav className="navigation">
      <button
        className="menu-toggle"
        onClick={toggleMenu}
        aria-label="메뉴 토글"
        aria-expanded={isOpen}
      >
        <span className="hamburger">
          <span></span>
          <span></span>
          <span></span>
        </span>
      </button>

      <ul className={`nav-menu ${isOpen ? "open" : ""}`}>
        {menuItems.map((item) => (
          <li key={item.id} className="nav-item">
            <button
              className={`nav-link ${currentView === item.id ? "active" : ""}`}
              onClick={() => handleNavClick(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Navigation;
