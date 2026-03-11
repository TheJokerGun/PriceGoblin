import React from "react";
import { Link } from "react-router-dom";
import { LuArrowLeft, LuPause, LuPlay } from "react-icons/lu";
import type { Tracking } from "../types";

interface ProductHeaderProps {
  tracking: Tracking | null;
  onToggleTracking: () => void;
}

const ProductHeader: React.FC<ProductHeaderProps> = ({
  tracking,
  onToggleTracking,
}) => {
  return (
    <div className="flex items-center justify-between">
      <Link to="/home" className="group flex items-center gap-2 dark:text-gray-400 text-gray-500 hover:dark:text-white hover:text-gray-900 transition-colors">
        <div className="p-2 dark:bg-gray-900 bg-gray-100 rounded-xl group-hover:dark:bg-gray-800 group-hover:bg-gray-200 transition-colors">
          <LuArrowLeft size={20} />
        </div>
        <span className="font-bold">Dashboard</span>
      </Link>
      
      {tracking && (
        <button
          onClick={onToggleTracking}
          className={`flex items-center gap-2 px-6 py-3 rounded-2xl font-bold transition-all shadow-lg active:scale-95 ${
            tracking.is_active 
              ? "dark:bg-red-900/40 bg-red-50 dark:border-red-500/30 border-red-200 text-red-500 dark:text-red-400 hover:dark:bg-red-800/50 hover:bg-red-100" 
              : "dark:bg-green-900/40 bg-green-50 dark:border-green-500/30 border-green-200 text-green-600 dark:text-green-400 hover:dark:bg-green-800/50 hover:bg-green-100"
          }`}
        >
          {tracking.is_active ? <LuPause size={18} /> : <LuPlay size={18} />}
          {tracking.is_active ? "Pause Watch" : "Resume Watch"}
        </button>
      )}
    </div>
  );
};

export default ProductHeader;
