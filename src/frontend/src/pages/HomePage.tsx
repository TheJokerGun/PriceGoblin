import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import type { Price, Product } from "../types";
import { readLocalStorageJson, writeLocalStorageJson } from "../utils/storage";

const PRICE_CACHE_KEY = "product_price_cache";
const PRICE_CACHE_DURATION_MS = 60 * 60 * 1000;

type CachedPrice = {
  price: number;
  timestamp: number;
};

type PriceCache = Record<number, CachedPrice>;

function HomePage() {
  const [url, setUrl] = useState("");
  const [isTracking, setIsTracking] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [isProductsLoading, setIsProductsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prices, setPrices] = useState<Record<number, number>>({});
  const [category, setCategory] = useState("general");

  const fetchProducts = useCallback(async () => {
    setIsProductsLoading(true);
    setError(null);
    try {
      const response = await api.get<Product[]>("/products");
      setProducts(response.data);
    } catch (err) {
      console.error("Error fetching products:", err);
      setError("Failed to fetch products.");
    } finally {
      setIsProductsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchProducts();
  }, [fetchProducts]);

  useEffect(() => {
    let isCancelled = false;

    const syncPrices = async () => {
      const now = Date.now();
      const cache = readLocalStorageJson<PriceCache>(PRICE_CACHE_KEY, {});
      const nextPrices: Record<number, number> = {};
      const idsToRefresh: number[] = [];

      for (const product of products) {
        const cachedItem = cache[product.id];
        if (cachedItem && now - cachedItem.timestamp < PRICE_CACHE_DURATION_MS) {
          nextPrices[product.id] = cachedItem.price;
          continue;
        }
        idsToRefresh.push(product.id);
      }

      if (!isCancelled) {
        setPrices(nextPrices);
      }

      if (idsToRefresh.length === 0) {
        return;
      }

      const updatedCache: PriceCache = { ...cache };
      const refreshedPrices: Record<number, number> = {};

      const refreshResults = await Promise.allSettled(
        idsToRefresh.map((productId) =>
          api.post<Price>(`/products/${productId}/check-price`),
        ),
      );

      refreshResults.forEach((result, index) => {
        const productId = idsToRefresh[index];
        if (result.status !== "fulfilled") {
          console.error(
            `Error fetching price for product ${productId}:`,
            result.reason,
          );
          return;
        }

        const price = Number(result.value.data.price);
        refreshedPrices[productId] = price;
        updatedCache[productId] = {
          price,
          timestamp: Date.now(),
        };
      });

      if (Object.keys(refreshedPrices).length > 0) {
        // Only write after successful fetches so we don't extend stale cache entries.
        writeLocalStorageJson(PRICE_CACHE_KEY, updatedCache);
      }

      if (!isCancelled && Object.keys(refreshedPrices).length > 0) {
        setPrices((prev) => ({ ...prev, ...refreshedPrices }));
      }
    };

    if (products.length > 0) {
      void syncPrices();
    } else {
      setPrices({});
    }

    return () => {
      isCancelled = true;
    };
  }, [products]);

  const handleTrackProduct = async () => {
    const normalizedUrl = url.trim();
    if (!normalizedUrl) {
      alert("Please enter a URL to track.");
      return;
    }

    setIsTracking(true);
    try {
      const payload = {
        name: "",
        url: normalizedUrl,
        category,
      };
      const response = await api.post<Product>("/products", payload);
      alert(`Product tracking started for: ${response.data.name ?? "Unknown product"}`);
      setUrl("");
      await fetchProducts();
    } catch (requestError) {
      console.error("Error tracking product:", requestError);
      alert("Failed to track product. Check console for details.");
    } finally {
      setIsTracking(false);
    }
  };

  const getDomain = (value: string | null) => {
    if (!value) {
      return "No URL";
    }
    try {
      return new URL(value).hostname;
    } catch {
      return value;
    }
  };

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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.map((product) => (
            <Link
              to={`/productinfo?id=${product.id}`}
              key={product.id}
              className="bg-purple-950 p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow block border-2 border-gray-400"
            >
              <h3
                className="font-bold text-lg truncate text-gray-300"
                title={product.name ?? "Unknown product"}
              >
                {product.name ?? "Unknown product"}
              </h3>
              {prices[product.id] !== undefined && (
                <p className="text-green-500 font-bold mt-2">
                  Price: {prices[product.id].toFixed(2)}
                </p>
              )}
              <p className="text-gray-400 text-sm break-all">
                {getDomain(product.url)}
              </p>
              <p className="text-gray-400 text-xs mt-2">
                Tracked since: {new Date(product.created_at).toLocaleDateString()}
              </p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

export default HomePage;
