import React from "react";
import { LuExternalLink, LuCalendar, LuTrendingDown, LuTrendingUp, LuDollarSign } from "react-icons/lu";
import type { Product } from "../types";

interface ProductStatsProps {
  product: Product;
  currentPrice: number | null;
  lowestPrice: number | null;
  highestPrice: number | null;
  targetPrice: number | null;
  onUpdateTargetPrice: (targetPrice: number | null) => void;
}

const ProductStats: React.FC<ProductStatsProps> = ({
  product,
  currentPrice,
  lowestPrice,
  highestPrice,
  targetPrice,
  onUpdateTargetPrice,
}) => {
  const [isEditing, setIsEditing] = React.useState(false);
  const [inputValue, setInputValue] = React.useState(targetPrice?.toString() || "");

  const handleSave = () => {
    const val = parseFloat(inputValue);
    if (!isNaN(val) && val >= 0) {
      onUpdateTargetPrice(val);
      setIsEditing(false);
    } else if (inputValue === "") {
      onUpdateTargetPrice(null);
      setIsEditing(false);
    }
  };

  const handleRemove = () => {
    onUpdateTargetPrice(null);
    setInputValue("");
    setIsEditing(false);
  };
  return (
    <div className="lg:col-span-1 space-y-6">
      <div className="bg-gray-900/50 backdrop-blur-md border border-gray-800 rounded-[2.5rem] p-8 shadow-2xl overflow-hidden relative">
        <div className="absolute top-0 right-0 p-8 opacity-5 text-8xl">
          <LuDollarSign />
        </div>
        
        <h1 className="text-3xl font-black mb-4 tracking-tight leading-tight" title={product.name}>
          {product.name}
        </h1>
        
        <a
          href={product.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 font-bold mb-8 bg-blue-500/10 px-4 py-2 rounded-xl transition-colors"
        >
          Shop Source <LuExternalLink size={14} />
        </a>

        <div className="grid grid-cols-2 gap-4 pt-6 border-t border-gray-800/50">
          <div className="space-y-1">
            <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Current Price</span>
            <p className="text-2xl font-black text-white">
              ${currentPrice?.toFixed(2) || "---"}
            </p>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Market Status</span>
            <div className="flex items-center gap-1.5 text-green-400 font-bold text-sm">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
              Monitoring
            </div>
          </div>
        </div>
      </div>

      <div className="bg-gray-900/40 backdrop-blur-md border border-gray-800 rounded-[2.5rem] p-8 shadow-2xl">
        <h3 className="text-gray-400 font-bold mb-6 uppercase tracking-widest text-[10px]">Target Price Alert</h3>
        
        {isEditing ? (
          <div className="space-y-4">
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 font-bold">$</span>
              <input
                type="number"
                step="0.01"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="299.99"
                className="w-full bg-black/50 border border-gray-700 rounded-2xl py-4 pl-8 pr-4 text-white font-bold focus:outline-hidden focus:border-blue-500 transition-colors"
                autoFocus
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={handleSave}
                className="py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold transition-all text-sm"
              >
                Set Target
              </button>
              <button
                onClick={() => setIsEditing(false)}
                className="py-3 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl font-bold transition-all text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-2xl font-black text-white">
                {targetPrice !== null ? `$${targetPrice.toFixed(2)}` : "Not Set"}
              </p>
              <p className="text-xs text-gray-500 font-medium">Notify when price drops below</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setIsEditing(true)}
                className="p-3 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl transition-all"
                title="Edit Target Price"
              >
                <LuDollarSign size={18} />
              </button>
              {targetPrice !== null && (
                <button
                  onClick={handleRemove}
                  className="p-3 bg-red-900/20 hover:bg-red-900/40 text-red-400 rounded-xl transition-all"
                  title="Remove Target Price"
                >
                  <LuTrendingDown size={18} />
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="bg-linear-to-br from-blue-600 to-indigo-700 rounded-[2.5rem] p-8 shadow-2xl relative overflow-hidden group">
        <div className="relative z-10">
          <h3 className="text-white font-bold opacity-80 mb-6 uppercase tracking-widest text-xs">Market Insights</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center text-white">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/20 rounded-xl"><LuTrendingDown size={20} /></div>
                <span className="font-medium">All-time Low</span>
              </div>
              <span className="font-black text-xl">${lowestPrice?.toFixed(2) || "---"}</span>
            </div>
            <div className="flex justify-between items-center text-white">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/20 rounded-xl"><LuTrendingUp size={20} /></div>
                <span className="font-medium">All-time High</span>
              </div>
              <span className="font-black text-xl">${highestPrice?.toFixed(2) || "---"}</span>
            </div>
          </div>
          <p className="mt-8 text-white/60 text-xs flex items-center gap-2">
            <LuCalendar size={14} /> Tracking since {new Date(product.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ProductStats;
