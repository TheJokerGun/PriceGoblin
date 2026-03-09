import React from "react";
import { Link } from "react-router-dom";
import { LuRefreshCw, LuPause, LuPlay, LuDelete } from "react-icons/lu";
import type { Product, Tracking } from "../types";

interface ProductCardProps {
  product: Product & { tracking?: Tracking };
  price: string | number | undefined;
  isRefreshing: boolean;
  onRefresh: (e: React.MouseEvent, productId: number) => void;
  onToggleTracking: (e: React.MouseEvent, trackingId: number) => void;
  onDelete: (e: React.MouseEvent, trackingId: number) => void;
}

const ProductCard: React.FC<ProductCardProps> = ({
  product,
  price,
  isRefreshing,
  onRefresh,
  onToggleTracking,
  onDelete,
}) => {
  const getDomain = (url: string) => {
    try {
      return new URL(url).hostname;
    } catch (e) {
      return url;
    }
  };

  return (
    <div
      key={product.id}
      className="group relative bg-gray-900/40 backdrop-blur-sm border border-gray-800 rounded-3xl p-6 transition-all hover:border-blue-500/50 hover:shadow-[0_0_30px_rgba(59,130,246,0.1)] overflow-hidden"
    >
      <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-all transform translate-y-2 group-hover:translate-y-0">
        <button
          onClick={(e) => onRefresh(e, product.id)}
          className={`p-2 bg-blue-600/20 text-blue-400 rounded-xl hover:bg-blue-600 hover:text-white transition-colors ${
            isRefreshing ? "animate-spin cursor-not-allowed" : ""
          }`}
          title="Refresh Price"
          disabled={isRefreshing}
        >
          <LuRefreshCw size={18} />
        </button>
        {product.tracking && (
          <>
            <button
              onClick={(e) => onToggleTracking(e, product.tracking!.id)}
              className="p-2 bg-gray-800/50 text-gray-300 rounded-xl hover:bg-gray-700 hover:text-white transition-colors"
              title={
                product.tracking.is_active ? "Pause Tracking" : "Resume Tracking"
              }
            >
              {product.tracking.is_active ? <LuPause size={18} /> : <LuPlay size={18} />}
            </button>
            <button
              onClick={(e) => onDelete(e, product.tracking!.id)}
              className="p-2 bg-red-900/20 text-red-400 rounded-xl hover:bg-red-600 hover:text-white transition-colors"
              title="Delete Tracking"
            >
              <LuDelete size={18} />
            </button>
          </>
        )}
      </div>

      <Link to={`/productinfo?id=${product.id}`} className="block">
        <h3
          className="font-bold text-xl text-white mb-2 line-clamp-1 group-hover:text-blue-400 transition-colors"
          title={product.name}
        >
          {product.name}
        </h3>
        <div className="flex flex-col gap-1 mb-4">
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-white">
              {price !== undefined ? (
                typeof price === 'number' ? price.toFixed(2) : price
              ) : (
                "---"
              )}
            </span>
            <span className="text-sm text-gray-500 font-medium">USD</span>
          </div>
          {product.tracking?.target_price !== undefined && product.tracking.target_price !== null && (
            <div className="flex items-center gap-1.5 text-[10px] font-bold text-blue-400/80 bg-blue-500/10 w-fit px-2 py-0.5 rounded-full">
              <span className="w-1 h-1 bg-blue-400 rounded-full"></span>
              Target: ${product.tracking.target_price.toFixed(2)}
            </div>
          )}
        </div>
        
        <div className="space-y-2">
          <p className="text-gray-400 text-sm flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-gray-600 rounded-full"></span>
            {getDomain(product.url)}
          </p>
          <p className="text-gray-500 text-xs mt-4 pt-4 border-t border-gray-800/50">
            Tracked since {new Date(product.created_at).toLocaleDateString()}
          </p>
        </div>
      </Link>
    </div>
  );
};

export default ProductCard;
