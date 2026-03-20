import React from "react";
import { Link } from "react-router-dom";
import { LuArrowLeft, LuPause, LuPlay, LuRefreshCw, LuDelete } from "react-icons/lu";
import type { Tracking } from "../types";

interface ProductHeaderProps {
  tracking: Tracking | null;
  onToggleTracking: () => void;
  isRefreshing: boolean;
  onRefresh: () => void;
  onDelete: () => void;
}

const ProductHeader: React.FC<ProductHeaderProps> = ({
  tracking,
  onToggleTracking,
  isRefreshing,
  onRefresh,
  onDelete,
}) => {
  return (
    <div className="flex items-center justify-between">
      <Link to="/home" className="group flex items-center gap-2 dark:text-gray-400 text-gray-500 hover:dark:text-white hover:text-gray-900 transition-colors">
        <div className="p-2 dark:bg-gray-900 bg-gray-100 rounded-xl group-hover:dark:bg-gray-800 group-hover:bg-gray-200 transition-colors">
          <LuArrowLeft size={20} />
        </div>
        <span className="font-bold">Dashboard</span>
      </Link>
      
      <div className="flex items-center gap-3">
        <button
          onClick={onRefresh}
          className={`flex items-center justify-center p-3 rounded-2xl transition-all shadow-lg active:scale-95 border ${
            isRefreshing
              ? "bg-blue-50 border-blue-200 text-blue-400 dark:bg-blue-900/40 dark:border-blue-500/30 cursor-not-allowed"
              : "bg-blue-50 border-blue-200 text-blue-500 hover:bg-blue-100 hover:border-blue-300 dark:bg-blue-900/40 dark:border-blue-500/30 dark:text-blue-400 dark:hover:bg-blue-800/50"
          }`}
          title="Refresh Price"
          disabled={isRefreshing}
        >
          <LuRefreshCw size={20} className={isRefreshing ? "animate-spin" : ""} />
        </button>

        {tracking && (
          <>
            <button
              onClick={onToggleTracking}
              className={`flex items-center gap-2 px-6 py-3 rounded-2xl font-bold transition-all shadow-lg active:scale-95 border ${
                tracking.is_active 
                  ? "dark:bg-yellow-900/40 bg-yellow-50 dark:border-yellow-500/30 border-yellow-200 text-yellow-600 dark:text-yellow-400 hover:dark:bg-yellow-800/50 hover:bg-yellow-100" 
                  : "dark:bg-green-900/40 bg-green-50 dark:border-green-500/30 border-green-200 text-green-600 dark:text-green-400 hover:dark:bg-green-800/50 hover:bg-green-100"
              }`}
            >
              {tracking.is_active ? <LuPause size={18} /> : <LuPlay size={18} />}
              {tracking.is_active ? "Pause Watch" : "Resume Watch"}
            </button>
            <button
              onClick={onDelete}
              className="flex items-center justify-center p-3 rounded-2xl transition-all shadow-lg active:scale-95 border bg-red-50 border-red-200 text-red-500 hover:bg-red-100 hover:border-red-300 dark:bg-red-900/40 dark:border-red-500/30 dark:text-red-400 dark:hover:bg-red-800/50"
              title="Delete Tracking"
            >
              <LuDelete size={20} />
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default ProductHeader;
