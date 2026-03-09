import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import type { Product, Tracking } from "../types";
import { LuDelete, LuPause, LuPlay, LuRefreshCw } from "react-icons/lu";

function HomePage() {
  const [url, setUrl] = useState("");
  const [isTracking, setIsTracking] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [trackings, setTrackings] = useState<Tracking[]>([]);
  const [isProductsLoading, setIsProductsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prices, setPrices] = useState<Record<number, string | number>>({});
  const [refreshing, setRefreshing] = useState<Record<number, boolean>>({});
  const [category, setCategory] = useState("general");

  const fetchData = async () => {
    setIsProductsLoading(true);
    try {
      const [productsRes, trackingsRes] = await Promise.all([
        api.get<Product[]>("/products"),
        api.get<Tracking[]>("/tracking"),
      ]);
      setProducts(productsRes.data);
      setTrackings(trackingsRes.data);
    } catch (err) {
      console.error("Error fetching products:", err);
      setError("Failed to fetch products.");
    } finally {
      setIsProductsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    products.forEach((product) => {
      api
        .get(`/products/${product.id}/current-price`)
        .then((response) => {
          setPrices((prev) => ({
            ...prev,
            [product.id]: response.data.price,
          }));
        })
        .catch((err) => {
          // If 404, it might not have any price entries yet.
          if (err.response?.status !== 404) {
            console.error(
              `Error fetching price for product ${product.id}:`,
              err,
            );
          }
        });
    });
  }, [products]);

  const handleTrackProduct = async () => {
    if (!url.trim()) {
      alert("Please enter a URL to track.");
      return;
    }

    setIsTracking(true);
    try {
      const payload = {
        name: "",
        url: url,
        category: category,
      };
      const response = await api.post("/products", payload);
      alert(`Product tracking started for: ${response.data.name}`);
      setUrl("");
      await fetchData();
    } catch (error) {
      console.error("Error tracking product:", error);
      alert("Failed to track product. Check console for details.");
    } finally {
      setIsTracking(false);
    }
  };

  const getDomain = (url: string) => {
    try {
      return new URL(url).hostname;
    } catch (e) {
      return url;
    }
  };

  const toggleTracking = async (e: React.MouseEvent, trackingId: number) => {
    e.preventDefault();
    try {
      await api.patch(`/tracking/${trackingId}/active`, {});
      setTrackings((prev) =>
        prev.map((t) =>
          t.id === trackingId ? { ...t, is_active: !t.is_active } : t,
        ),
      );
    } catch (err) {
      console.error("Error toggling tracking:", err);
    }
  };

  const deleteTracking = async (e: React.MouseEvent, trackingId: number) => {
    e.preventDefault();
    if (!confirm("Are you sure you want to delete this tracking?")) return;
    try {
      await api.delete(`/tracking/${trackingId}`);
      setTrackings((prev) => prev.filter((t) => t.id !== trackingId));
    } catch (err) {
      console.error("Error deleting tracking:", err);
    }
  };

  const refreshPrice = async (e: React.MouseEvent, productId: number) => {
    e.preventDefault();
    setRefreshing((prev) => ({ ...prev, [productId]: true }));
    try {
      const response = await api.post(`/products/${productId}/check-price`);
      setPrices((prev) => ({
        ...prev,
        [productId]: response.data.price,
      }));
    } catch (err) {
      console.error(`Error refreshing price for product ${productId}:`, err);
    } finally {
      setRefreshing((prev) => ({ ...prev, [productId]: false }));
    }
  };

  const getProductWithTracking = () => {
    return products
      .map((p) => {
        const t = trackings.find((tr) => tr.product_id === p.id);
        return { ...p, tracking: t };
      })
      .filter((item) => item.tracking);
  };

  const combined = getProductWithTracking();
  const activeProducts = combined.filter((p) => p.tracking?.is_active);
  const inactiveProducts = combined.filter((p) => !p.tracking?.is_active);

  const renderProductCard = (
    product: Product & { tracking: Tracking | undefined },
  ) => (
    <Link
      to={`/productinfo?id=${product.id}`}
      key={product.id}
      className="bg-purple-950 p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow block border-2 border-gray-400 relative group"
    >
      <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={(e) => refreshPrice(e, product.id)}
          className={`p-1 bg-blue-800 rounded hover:bg-blue-700 text-white ${refreshing[product.id] ? "animate-spin cursor-not-allowed" : ""}`}
          title="Refresh Price"
          disabled={refreshing[product.id]}
        >
          <LuRefreshCw />
        </button>
        <button
          onClick={(e) => toggleTracking(e, product.tracking!.id)}
          className="p-1 bg-gray-800 rounded hover:bg-gray-700 text-white"
          title={
            product.tracking!.is_active ? "Pause Tracking" : "Resume Tracking"
          }
        >
          {product.tracking!.is_active ? <LuPause /> : <LuPlay />}
        </button>
        <button
          onClick={(e) => deleteTracking(e, product.tracking!.id)}
          className="p-1 bg-red-800 rounded hover:bg-red-700 text-white"
          title="Delete Tracking"
        >
          <LuDelete />
        </button>
      </div>
      <h3
        className="font-bold text-lg truncate text-gray-300 pr-16"
        title={product.name}
      >
        {product.name}
      </h3>
      {prices[product.id] !== undefined && (
        <p className="text-green-500 font-bold mt-2">
          Price: {prices[product.id]}
        </p>
      )}
      <p className="text-gray-400 text-sm break-all">
        {getDomain(product.url)}
      </p>
      <p className="text-gray-400 text-xs mt-2">
        Tracked since: {new Date(product.created_at).toLocaleDateString()}
      </p>
    </Link>
  );

  return (
    <div className="container mx-auto p-4">
      <div className="w-full max-w-md mx-auto flex flex-col gap-4 mb-8">
        <h2 className="text-2xl font-bold text-center text-white">
          Track a New Product
        </h2>
        <input
          type="text"
          placeholder="Enter product URL to track"
          className="p-3 border border-gray-300 bg-gray-100 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="p-3 border border-gray-300 bg-gray-100 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="general">General</option>
          <option value="cards">Cards</option>
          <option value="games">Game Keys</option>
        </select>
        <button
          onClick={handleTrackProduct}
          disabled={isTracking}
          className={`bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 transition ${isTracking ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          {isTracking ? "Tracking..." : "Track Product"}
        </button>
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-4 text-white">
          Your Tracked Products
        </h2>
        {isProductsLoading && <p>Loading products...</p>}
        {error && <p className="text-red-500">{error}</p>}
        {!isProductsLoading && !error && products.length === 0 && (
          <p>You are not tracking any products yet.</p>
        )}

        {activeProducts.length > 0 && (
          <>
            <h3 className="text-xl font-bold mb-4 text-green-400">Active</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {activeProducts.map((product) => renderProductCard(product))}
            </div>
          </>
        )}

        {inactiveProducts.length > 0 && (
          <>
            <h3 className="text-xl font-bold mb-4 text-gray-400">Inactive</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {inactiveProducts.map((product) => renderProductCard(product))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default HomePage;
