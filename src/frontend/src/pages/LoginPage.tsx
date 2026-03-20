import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import { LuLogIn, LuUserPlus, LuMail, LuLock, LuShieldCheck, LuGithub } from "react-icons/lu";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/home");
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError("");
      }, 10000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    if (import.meta.env.VITE_SKIP_LOGIN === "true") {
      console.log("Skipping real login for development.");
      login("dummy-dev-token");
      setIsLoading(false);
      return;
    }

    try {
      const endpoint = isRegistering ? "/auth/register" : "/auth/login";
      const response = await api.post(endpoint, { 
        email, 
        password: btoa(password),
        locale: navigator.language 
      });
      login(response.data.access_token);
    } catch (err: any) {
      console.error(err);
      const rawDetail = err.response?.data?.detail;
      const detail = typeof rawDetail === "string"
        ? rawDetail
        : (rawDetail ? JSON.stringify(rawDetail) : (isRegistering ? "Registration failed." : "Login failed."));
      setError(detail);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center dark:bg-black bg-gray-50 overflow-hidden relative transition-colors duration-300">
      {/* Decorative background elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] dark:bg-blue-600/20 bg-blue-500/5 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] dark:bg-purple-600/20 bg-purple-500/5 rounded-full blur-[120px]" />
      
      <div className="w-full max-w-md px-4 z-10">
        <div className="text-center mb-10">
          <div className="inline-flex p-4 bg-linear-to-br from-blue-500 to-indigo-600 rounded-3xl shadow-[0_0_30px_rgba(59,130,246,0.3)] mb-6">
            <LuShieldCheck className="text-white text-4xl" />
          </div>
          <h1 className="text-4xl font-black dark:text-white text-gray-900 tracking-tight mb-2">
            PriceGoblin
          </h1>
          <p className="dark:text-gray-500 text-gray-400 font-medium">Watch prices fall, not your savings.</p>
        </div>

        <div className="dark:bg-gray-900/40 bg-white backdrop-blur-2xl p-8 rounded-[2.5rem] border dark:border-gray-800 border-gray-200 shadow-2xl">
          <div className="flex dark:bg-black/40 bg-gray-50 p-1 rounded-2xl mb-8 border dark:border-gray-800/50 border-gray-200">
            <button
              onClick={() => setIsRegistering(false)}
              className={`flex-1 py-3 px-4 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 ${!isRegistering ? "dark:bg-gray-800 bg-white dark:text-white text-gray-900 shadow-lg" : "text-gray-500 hover:text-gray-300"}`}
            >
              <LuLogIn size={18} /> Sign In
            </button>
            <button
              onClick={() => setIsRegistering(true)}
              className={`flex-1 py-3 px-4 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 ${isRegistering ? "dark:bg-gray-800 bg-white dark:text-white text-gray-900 shadow-lg" : "text-gray-500 hover:text-gray-300"}`}
            >
              <LuUserPlus size={18} /> Join
            </button>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-4 rounded-2xl mb-6 text-sm font-medium animate-pulse">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-widest ml-1">Email Address</label>
              <div className="relative">
                <LuMail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="email"
                  value={email}
                  placeholder="name@company.com"
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full p-4 pl-12 dark:bg-black/40 bg-gray-50 border dark:border-gray-800 border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white text-gray-900 placeholder-gray-400 transition-all font-medium"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-widest ml-1">Secret Password</label>
              <div className="relative">
                <LuLock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="password"
                  value={password}
                  placeholder="••••••••"
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full p-4 pl-12 dark:bg-black/40 bg-gray-50 border dark:border-gray-800 border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white text-gray-900 placeholder-gray-400 transition-all font-medium"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-linear-to-r from-blue-600 to-indigo-600 text-white font-bold py-5 rounded-2xl hover:from-blue-500 hover:to-indigo-500 transition-all shadow-xl shadow-blue-900/10 active:scale-[0.98] border border-blue-400/20 disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              {isLoading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Processing...
                </div>
              ) : (
                <div className="flex items-center justify-center gap-2">
                  {isRegistering ? "Create Account" : "Access Watchlist"}
                  <LuLogIn className="group-hover:translate-x-1 transition-transform" />
                </div>
              )}
            </button>
          </form>

          <div className="mt-8 pt-8 border-t dark:border-gray-800/50 border-gray-100">
            <p className="text-center dark:text-gray-600 text-gray-400 text-xs font-medium mb-4 italic">
              "The best price is the one you track."
            </p>
            <div className="flex items-center justify-center gap-4 dark:text-gray-500 text-gray-400">
              <button
                onClick={() => window.open("https://github.com/TheJokerGun/PriceGoblin", "_blank")}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"><LuGithub size={20} /></button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;

