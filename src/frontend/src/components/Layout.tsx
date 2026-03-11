import React from "react";
import { useNavigate, Link } from "react-router-dom";
import { LuLogOut } from "react-icons/lu";
import { useAuth } from "../context/AuthContext";
import ThemeToggle from "./ThemeToggle";

import logo from "../assets/logo.png";

const Layout: React.FC<React.PropsWithChildren<{}>> = ({ children }) => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen dark:bg-black bg-gray-50 dark:text-white text-gray-900 selection:bg-blue-500/30 transition-colors duration-300">
      {/* Dynamic background element */}
      <div className="fixed top-0 left-0 w-full h-full pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] dark:bg-blue-900/10 bg-blue-500/5 rounded-full blur-[160px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] dark:bg-indigo-900/10 bg-indigo-500/5 rounded-full blur-[140px]" />
      </div>

      <header className="sticky top-0 z-50 border-b dark:border-white/5 border-gray-200 dark:bg-black/60 bg-white/60 backdrop-blur-xl">
        <div className="container mx-auto flex items-center justify-between p-4 px-6 md:px-12">
          <Link to="/home" className="flex items-center gap-4 group">
            <div className="p-2 dark:bg-white/5 bg-gray-100 rounded-2xl border dark:border-white/5 border-gray-200 shadow-lg group-hover:scale-110 transition-all flex items-center justify-center overflow-hidden w-16 h-16">
              <img src={logo} alt="PriceGoblin Logo" className="w-full h-full object-contain scale-110" />
            </div>
            <span className="text-3xl font-black tracking-tight dark:bg-linear-to-r dark:from-white dark:to-gray-400 bg-linear-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
              PriceGoblin
            </span>
          </Link>

          <div className="flex items-center gap-4 md:gap-6">
            <ThemeToggle />
            {isAuthenticated && (
              <button
                onClick={handleLogout}
                className="p-2.5 dark:bg-white/5 bg-gray-100 hover:dark:bg-white/10 hover:bg-gray-200 text-gray-400 dark:hover:text-white hover:text-gray-900 rounded-2xl border dark:border-white/5 border-gray-200 transition-all shadow-sm active:scale-95 group"
                title="Log Out"
              >
                <LuLogOut size={22} className="group-hover:-translate-x-0.5 transition-transform" />
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="relative z-10 container mx-auto py-8">
        {children}
      </main>

      <footer className="relative z-10 border-t dark:border-white/5 border-gray-200 py-12 dark:bg-black/40 bg-gray-100/40">
        <div className="container mx-auto px-6 text-center space-y-4">
          <p className="dark:text-gray-600 text-gray-400 text-sm font-medium">
            &copy; 2026 PriceGoblin. Hunting discounts around the clock.
          </p>
          <div className="flex justify-center gap-6">
            <Link to="/impressum" className="text-xs font-bold dark:text-gray-700 text-gray-400 hover:dark:text-blue-400 hover:text-blue-600 transition-colors uppercase tracking-widest">
              Impressum
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
