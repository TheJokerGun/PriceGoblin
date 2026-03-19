import React from "react";
import { useNavigate } from "react-router-dom";
import logo from "../assets/logo.png";
import { FiLogIn, FiLogOut } from "react-icons/fi";
import { useAuth } from "../context/AuthContext";

const Layout: React.FC<React.PropsWithChildren> = ({ children }) => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleAuthClick = () => {
    if (isAuthenticated) {
      logout();
    }
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-blend-hue bg-green-900">
      <header className="container mx-auto flex items-center justify-between p-4 mb-8">
        <div className="flex items-center gap-4">
          <img src={logo} alt="PriceGoblin Logo" className="w-16 h-16" />
          <h1 className="text-5xl font-extrabold text-white tracking-tight">
            PriceGoblin
          </h1>
        </div>
        <button
          onClick={handleAuthClick}
          className="bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 transition"
          aria-label={isAuthenticated ? "Log Out" : "Log In"}
        >
          {isAuthenticated ? <FiLogOut size={24} /> : <FiLogIn size={24} />}
        </button>
      </header>
      <main className="flex justify-center px-4">{children}</main>
    </div>
  );
};

export default Layout;
