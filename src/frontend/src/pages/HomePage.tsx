import { useState } from "react";
import logo from "../assets/logo.png";
import api from '../api/client';

function HomePage() {
  const [url, setUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleTrackProduct = async () => {
    if (!url.trim()) {
      alert("Please enter a URL to track.");
      return;
    }

    setIsLoading(true);
    try {
      const payload = {
        name: "",
        url: url,
        category: "",
      };
      const response = await api.post("/scrape", payload);
      alert(`Product tracking started for: ${response.data.name}`);
      setUrl("");
    } catch (error) {
      console.error("Error tracking product:", error);
      alert("Failed to track product. Check console for details.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-blend-hue bg-green-900 p-4">
      <div className="flex items-center gap-4 mb-8">
        <img src={logo} alt="PriceGoblin Logo" className="w-32 h-32" />
        <h1 className="text-5xl font-extrabold text-gray-900 tracking-tight">
          Welcome to PriceGoblin
        </h1>
      </div>
      <div className="w-full max-w-md flex flex-col gap-4">
        <input
          type="text"
          placeholder="Enter product URL to track"
          className="p-3 border border-gray-300 bg-gray-100 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button
          onClick={handleTrackProduct}
          disabled={isLoading}
          className={`bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 transition ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}>
          {isLoading ? "Tracking..." : "Track Product"}
        </button>
      </div>
    </div>
  );
}

export default HomePage;