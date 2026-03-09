import React from "react";
import { useNavigate, Link } from "react-router-dom";
import { LuLogOut } from "react-icons/lu";
import { useAuth } from "../context/AuthContext";

import logo from "../assets/logo.png";

const Layout: React.FC<React.PropsWithChildren<{}>> = ({ children }) => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-black text-white selection:bg-blue-500/30">
      {/* Dynamic background element */}
      <div className="fixed top-0 left-0 w-full h-full pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-blue-900/10 rounded-full blur-[160px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-900/10 rounded-full blur-[140px]" />
      </div>

      <header className="sticky top-0 z-50 border-b border-white/5 bg-black/60 backdrop-blur-xl">
        <div className="container mx-auto flex items-center justify-between p-4 px-6 md:px-12">
          <Link to="/home" className="flex items-center gap-4 group">
            <div className="p-2 bg-white/5 rounded-2xl border border-white/5 shadow-lg group-hover:scale-110 transition-all flex items-center justify-center overflow-hidden w-16 h-16">
              <img src={logo} alt="PriceGoblin Logo" className="w-full h-full object-contain scale-110" />
            </div>
            <span className="text-3xl font-black tracking-tight bg-linear-to-r from-white to-gray-400 bg-clip-text text-transparent">
              PriceGoblin
            </span>
          </Link>

          {isAuthenticated && (
            <div className="flex items-center gap-6">
              <button
                onClick={handleLogout}
                className="p-2.5 bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white rounded-2xl border border-white/5 transition-all shadow-sm active:scale-95 group"
                title="Log Out"
              >
                <LuLogOut size={22} className="group-hover:-translate-x-0.5 transition-transform" />
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="relative z-10 container mx-auto py-8">
        {children}
      </main>

      <footer className="relative z-10 border-t border-white/5 py-12 bg-black/40">
        <div className="container mx-auto px-6 text-center">
          <p className="text-gray-600 text-sm font-medium">
            &copy; 2026 PriceGoblin. Hunting discounts around the clock.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
