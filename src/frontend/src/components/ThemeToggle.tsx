import React from "react";
import { LuSun, LuMoon } from "react-icons/lu";
import { useTheme } from "../context/ThemeContext";

const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="p-2.5 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-2xl border border-gray-200 dark:border-white/5 transition-all shadow-sm active:scale-95 flex items-center justify-center"
      title={theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
    >
      {theme === "light" ? <LuMoon size={22} /> : <LuSun size={22} />}
    </button>
  );
};

export default ThemeToggle;
