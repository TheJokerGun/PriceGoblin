import React from "react";
import { LuExternalLink, LuCalendar, LuTrendingDown, LuTrendingUp, LuDollarSign } from "react-icons/lu";
import type { Product } from "../types";
import { formatCurrency, formatDate } from "../utils/formatters";

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
      <div className="dark:bg-gray-900/50 bg-white backdrop-blur-md border dark:border-gray-800 border-gray-200 rounded-[2.5rem] p-8 shadow-2xl overflow-hidden relative transition-colors duration-300">
        <div className="absolute top-0 right-0 p-8 opacity-5 text-8xl">
          <LuDollarSign />
        </div>
        
        <div className="flex flex-col gap-6 mb-8 relative z-10">
          <div className="w-full aspect-square rounded-4xl overflow-hidden dark:bg-gray-800/50 bg-gray-50 flex items-center justify-center border dark:border-gray-700/50 border-gray-200 shrink-0">
            {product.image_url ? (
              <img 
                src={product.image_url} 
                alt={product.name}
                className="w-full h-full object-cover transition-transform duration-500 hover:scale-110"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'https://via.placeholder.com/400x400?text=No+Image';
                }}
              />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center text-gray-600 gap-1 scale-75">
                <span className="text-3xl">📦</span>
                <span className="text-[8px] font-bold uppercase tracking-widest text-center">No Image</span>
              </div>
            )}
          </div>
          <div className="space-y-4">
            <h1 className="text-3xl font-black tracking-tight leading-tight dark:text-white text-gray-900" title={product.name}>
              {product.name}
            </h1>
            
            <a
              href={product.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 font-bold bg-blue-500/10 px-4 py-2 rounded-xl transition-colors w-fit"
            >
              Shop Source <LuExternalLink size={14} />
            </a>
          </div>
        </div>
<div className="grid grid-cols-2 gap-4 pt-6 border-t dark:border-gray-800/50 border-gray-100">
          <div className="space-y-1">
            <span className="text-[10px] font-black dark:text-gray-500 text-gray-400 uppercase tracking-widest">Current Price</span>
            <p className="text-2xl font-black dark:text-white text-gray-900">
              {formatCurrency(currentPrice)}
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

      <div className="dark:bg-gray-900/40 bg-white backdrop-blur-md border dark:border-gray-800 border-gray-200 rounded-[2.5rem] p-8 shadow-2xl transition-colors duration-300">
        <h3 className="dark:text-gray-400 text-gray-500 font-bold mb-6 uppercase tracking-widest text-[10px]">Target Price Alert</h3>
        
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
                className="w-full dark:bg-black/50 bg-gray-50 border dark:border-gray-700 border-gray-200 rounded-2xl py-4 pl-8 pr-4 dark:text-white text-gray-900 font-bold focus:outline-hidden focus:ring-2 focus:ring-blue-500 transition-colors"
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
                className="py-3 dark:bg-gray-800 bg-gray-100 hover:dark:bg-gray-700 hover:bg-gray-200 dark:text-gray-300 text-gray-600 rounded-xl font-bold transition-all text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-2xl font-black dark:text-white text-gray-900">
                {targetPrice !== null ? formatCurrency(targetPrice) : "Not Set"}
              </p>
              <p className="text-xs text-gray-500 font-medium">Notify when price drops below</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setIsEditing(true)}
                className="p-3 dark:bg-gray-800 bg-gray-100 hover:dark:bg-gray-700 hover:bg-gray-200 dark:text-gray-300 text-gray-600 rounded-xl transition-all"
                title="Edit Target Price"
              >
                <LuDollarSign size={18} />
              </button>
              {targetPrice !== null && (
                <button
                  onClick={handleRemove}
                  className="p-3 dark:bg-red-900/20 bg-red-50 hover:dark:bg-red-900/40 hover:bg-red-100 text-red-500 dark:text-red-400 rounded-xl transition-all"
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
              <span className="font-black text-xl">{formatCurrency(lowestPrice)}</span>
            </div>
            <div className="flex justify-between items-center text-white">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/20 rounded-xl"><LuTrendingUp size={20} /></div>
                <span className="font-medium">All-time High</span>
              </div>
              <span className="font-black text-xl">{formatCurrency(highestPrice)}</span>
            </div>
          </div>
          <p className="mt-8 text-white/60 text-xs flex items-center gap-2">
            <LuCalendar size={14} /> Tracking since {formatDate(product.created_at)}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ProductStats;
