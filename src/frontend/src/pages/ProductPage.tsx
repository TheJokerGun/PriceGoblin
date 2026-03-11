import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import type { Product, Price, Tracking } from "../types";
import api from "../api/client";
import { showAlert } from "../utils/alerts";
import { formatDate } from "../utils/formatters";
import { LuArrowLeft } from "react-icons/lu";

import ProductHeader from "../components/ProductHeader";
import ProductStats from "../components/ProductStats";
import PriceChart from "../components/PriceChart";

const ProductPage = () => {
  const [searchParams] = useSearchParams();
  const id = searchParams.get("id");
  const [product, setProduct] = useState<Product | null>(null);
  const [prices, setPrices] = useState<Price[]>([]);
  const [tracking, setTracking] = useState<Tracking | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProductData = async () => {
      if (!id) return;

      setLoading(true);
      setError(null);
      try {
        const [productResponse, pricesResponse] = await Promise.all([
          api.get<Product>(`/products/${id}`),
          api.get<Price[]>(`/products/${id}/prices`),
        ]);

        setProduct(productResponse.data);
        setPrices(pricesResponse.data);
      } catch (err) {
        console.error("Error fetching product data:", err);
        setError("Failed to fetch product data.");
      } finally {
        setLoading(false);
      }
    };

    fetchProductData();
  }, [id]);

  useEffect(() => {
    const fetchTracking = async () => {
      if (!id) return;
      try {
        const res = await api.get<Tracking[]>("/tracking");
        const t = res.data.find((tr) => tr.product_id === Number(id));
        setTracking(t || null);
      } catch (e) {
        console.error("Error fetching tracking status", e);
      }
    };
    fetchTracking();
  }, [id]);

  const handleToggleTracking = async () => {
    if (!tracking) return;
    try {
      await api.patch(`/tracking/${tracking.id}/active`, {});
      setTracking({ ...tracking, is_active: !tracking.is_active });
    } catch (e) {
      console.error("Error toggling tracking", e);
      showAlert("Failed to toggle status");
    }
  };

  const handleUpdateTargetPrice = async (targetPrice: number | null) => {
    if (!tracking) return;
    try {
      await api.patch(`/tracking/${tracking.id}/target-price`, { target_price: targetPrice });
      setTracking({ ...tracking, target_price: targetPrice });
    } catch (e) {
      console.error("Error updating target price", e);
      showAlert("Failed to update target price");
    }
  };

  const formattedPrices = prices.map((p) => ({
    date: formatDate(p.checked_at, { month: 'short', day: 'numeric' }),
    fullDate: formatDate(p.checked_at, { dateStyle: 'medium', timeStyle: 'short' }),
    price: Number(p.price),
  }));

  const currentPrice = prices.length > 0 ? Number(prices[prices.length - 1].price) : null;
  const lowestPrice = prices.length > 0 ? Math.min(...prices.map(p => Number(p.price))) : null;
  const highestPrice = prices.length > 0 ? Math.max(...prices.map(p => Number(p.price))) : null;

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center dark:text-gray-500 text-gray-400">
        <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mb-4" />
        <p className="animate-pulse font-medium">Analyzing market data...</p>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center">
        <div className="p-4 bg-red-900/20 border border-red-500/50 rounded-2xl text-red-400 mb-6 max-w-md">
          {error || "Product not found."}
        </div>
        <Link to="/home" className="text-blue-400 hover:text-blue-300 flex items-center gap-2 font-bold transition-colors">
          <LuArrowLeft /> Return to Watchlist
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 dark:text-white text-gray-900 space-y-8 transition-colors duration-300">
      <ProductHeader tracking={tracking} onToggleTracking={handleToggleTracking} />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <ProductStats
          product={product}
          currentPrice={currentPrice}
          lowestPrice={lowestPrice}
          highestPrice={highestPrice}
          targetPrice={tracking?.target_price ?? null}
          onUpdateTargetPrice={handleUpdateTargetPrice}
        />
        <PriceChart prices={formattedPrices} />
      </div>
    </div>
  );
};

export default ProductPage;

