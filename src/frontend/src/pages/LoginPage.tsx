import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/home");
    }
  }, [isAuthenticated, navigate]);

  const authenticate = async (path: "/auth/login" | "/auth/register") => {
    setIsSubmitting(true);
    try {
      const response = await api.post(path, { email, password });
      login(response.data.access_token);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");

    if (import.meta.env.VITE_SKIP_LOGIN === "true") {
      console.log("Skipping real login for development.");
      login("dummy-dev-token");
      return;
    }

    try {
      await authenticate("/auth/login");
    } catch (err) {
      console.error(err);
      setError("Login failed. Please check your credentials.");
    }
  };

  const handleRegister = async (e: React.MouseEvent) => {
    e.preventDefault();
    setError("");

    try {
      await authenticate("/auth/register");
    } catch (err) {
      console.error(err);
      setError("Registration failed. Please try again.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-green-900 px-4">
      <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">
          Login to PriceGoblin
        </h2>
        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded mb-4 text-sm">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div className="flex gap-4">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-blue-600 text-white font-bold py-3 rounded hover:bg-blue-700 transition duration-200"
            >
              {isSubmitting ? "Working..." : "Log In"}
            </button>
            <button
              type="button"
              onClick={handleRegister}
              disabled={isSubmitting}
              className="flex-1 bg-green-600 text-white font-bold py-3 rounded hover:bg-green-700 transition duration-200"
            >
              {isSubmitting ? "Working..." : "Register"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
