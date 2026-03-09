import React from "react";
import { LuRefreshCw } from "react-icons/lu";

interface SearchSectionProps {
  url: string;
  setUrl: (url: string) => void;
  category: string;
  setCategory: (category: string) => void;
  handleTrackProduct: () => void;
  isTracking: boolean;
}

const SearchSection: React.FC<SearchSectionProps> = ({
  url,
  setUrl,
  category,
  setCategory,
  handleTrackProduct,
  isTracking,
}) => {
  return (
    <div className="w-full max-w-xl mx-auto flex flex-col gap-6 mb-12 p-8 bg-gray-900/50 backdrop-blur-md rounded-3xl border border-gray-800 shadow-2xl">
      <h2 className="text-3xl font-extrabold text-center bg-linear-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent italic">
        The Hunt Begins
      </h2>
      <div className="space-y-4">
        <div className="relative">
          <input
            type="text"
            placeholder="Enter URL or product name..."
            className="w-full p-4 pl-12 bg-black/40 border border-gray-700 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-500 transition-all"
            value={url}
            onKeyDown={(e) => e.key === "Enter" && handleTrackProduct()}
            onChange={(e) => setUrl(e.target.value)}
          />
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">
            <LuRefreshCw className={isTracking ? "animate-spin text-blue-500" : ""} />
          </div>
        </div>
        <div className="flex gap-4">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="flex-1 p-4 bg-black/40 border border-gray-700 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-white transition-all appearance-none cursor-pointer"
          >
            <option value="general">General</option>
            <option value="cards">Cards</option>
            <option value="games">Game Keys</option>
          </select>
          <button
            onClick={handleTrackProduct}
            disabled={isTracking}
            className={`flex-1 bg-linear-to-r from-blue-600 to-indigo-600 text-white font-bold py-4 px-6 rounded-2xl hover:from-blue-500 hover:to-indigo-500 transition-all shadow-lg active:scale-95 border border-blue-400/20 ${
              isTracking ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            {isTracking ? "Searching..." : "Track Product"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SearchSection;
