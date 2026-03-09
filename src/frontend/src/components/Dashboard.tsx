import React from "react";
import { LuRefreshCw } from "react-icons/lu";
import type { Product, Tracking } from "../types";
import ProductCard from "./ProductCard";

interface DashboardProps {
  isLoading: boolean;
  error: string | null;
  products: Product[];
  activeProducts: (Product & { tracking?: Tracking })[];
  inactiveProducts: (Product & { tracking?: Tracking })[];
  prices: Record<number, string | number>;
  refreshing: Record<number, boolean>;
  onRefreshPrice: (e: React.MouseEvent, productId: number) => void;
  onToggleTracking: (e: React.MouseEvent, trackingId: number) => void;
  onDeleteTracking: (e: React.MouseEvent, trackingId: number) => void;
}

const Dashboard: React.FC<DashboardProps> = ({
  isLoading,
  error,
  products,
  activeProducts,
  inactiveProducts,
  prices,
  refreshing,
  onRefreshPrice,
  onToggleTracking,
  onDeleteTracking,
}) => {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-white flex items-center gap-3">
        <span className="w-2 h-8 bg-blue-500 rounded-full"></span>
        Your Dashboard
      </h2>

      {isLoading && (
        <div className="flex flex-col items-center justify-center p-20 text-gray-500">
          <LuRefreshCw className="animate-spin text-4xl mb-4" />
          <p className="animate-pulse font-medium">Fetching your products...</p>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-900/20 border border-red-500/50 rounded-xl text-red-400 mb-6">
          {error}
        </div>
      )}

      {!isLoading && !error && products.length === 0 && (
        <div className="text-center p-20 bg-gray-900/20 rounded-4xl border-2 border-dashed border-gray-800">
          <p className="text-gray-400 text-lg font-medium">Your watchlist is empty.</p>
          <p className="text-gray-600 text-sm mt-2 font-medium italic">Start by adding a product above!</p>
        </div>
      )}

      {products.length > 0 && (
        <div className="space-y-12">
          {activeProducts.length > 0 && (
            <section>
              <h3 className="text-lg font-semibold mb-6 text-blue-400/80 uppercase tracking-widest flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-ping"></span>
                Active Monitoring
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {activeProducts.map((p) => (
                  <ProductCard
                    key={p.id}
                    product={p}
                    price={prices[p.id]}
                    isRefreshing={refreshing[p.id]}
                    onRefresh={onRefreshPrice}
                    onToggleTracking={onToggleTracking}
                    onDelete={onDeleteTracking}
                  />
                ))}
              </div>
            </section>
          )}

          {inactiveProducts.length > 0 && (
            <section>
              <h3 className="text-lg font-semibold mb-6 text-gray-500 uppercase tracking-widest">
                Paused
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 opacity-60 grayscale hover:opacity-100 hover:grayscale-0 transition-all">
                {inactiveProducts.map((p) => (
                  <ProductCard
                    key={p.id}
                    product={p}
                    price={prices[p.id]}
                    isRefreshing={refreshing[p.id]}
                    onRefresh={onRefreshPrice}
                    onToggleTracking={onToggleTracking}
                    onDelete={onDeleteTracking}
                  />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
