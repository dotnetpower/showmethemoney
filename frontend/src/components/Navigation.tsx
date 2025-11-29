import { useState } from "react";

interface NavigationProps {
  currentView: string;
  onViewChange: (view: string) => void;
}

const Navigation = ({ currentView, onViewChange }: NavigationProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const menuItems = [
    { id: "etf-list", label: "전체 ETF" },
    { id: "dividend-schedule", label: "배당 일정" },
    { id: "total-return", label: "Total Return" },
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
              {item.label}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Navigation;
