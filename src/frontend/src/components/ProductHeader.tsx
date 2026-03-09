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
      <Link to="/home" className="group flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
        <div className="p-2 bg-gray-900 rounded-xl group-hover:bg-gray-800 transition-colors">
          <LuArrowLeft size={20} />
        </div>
        <span className="font-bold">Dashboard</span>
      </Link>
      
      {tracking && (
        <button
          onClick={onToggleTracking}
          className={`flex items-center gap-2 px-6 py-3 rounded-2xl font-bold transition-all shadow-lg active:scale-95 ${
            tracking.is_active 
              ? "bg-red-900/40 border border-red-500/30 text-red-400 hover:bg-red-800/50" 
              : "bg-green-900/40 border border-green-500/30 text-green-400 hover:bg-green-800/50"
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
