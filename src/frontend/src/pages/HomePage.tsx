import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from '../api/client';

interface Product {
  id: number;
  name: string;
  url: string;
  category: string | null;
  created_at: string;
}

function HomePage() {
  const [url, setUrl] = useState("");
  const [isTracking, setIsTracking] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [isProductsLoading, setIsProductsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prices, setPrices] = useState<Record<number, string | number>>({});

  const fetchProducts = async () => {
    setIsProductsLoading(true);
    try {
      const response = await api.get<Product[]>("/products");
      setProducts(response.data);
    } catch (err) {
      console.error("Error fetching products:", err);
      setError("Failed to fetch products.");
    } finally {
      setIsProductsLoading(false);
    }
  };

  useEffect(() => {1
    fetchProducts();
  }, []);

  useEffect(() => {
    const CACHE_KEY = 'product_price_cache';
    const CACHE_DURATION = 60 * 60 * 1000; // 1 hour
    const now = Date.now();
    const cachedData = localStorage.getItem(CACHE_KEY);
    const cache = cachedData ? JSON.parse(cachedData) : {};

    products.forEach((product) => {
      const cachedItem = cache[product.id];
      if (cachedItem && (now - cachedItem.timestamp < CACHE_DURATION)) {
        setPrices((prev) => ({ ...prev, [product.id]: cachedItem.price }));
      } else {
        api.post(`/products/${product.id}/check-price`)
          .then((response) => {
            setPrices((prev) => ({ ...prev, [product.id]: response.data.price }));
            const currentCache = JSON.parse(localStorage.getItem(CACHE_KEY) || '{}');
            currentCache[product.id] = { price: response.data.price, timestamp: Date.now() };
            localStorage.setItem(CACHE_KEY, JSON.stringify(currentCache));
          })
          .catch((err) => console.error(`Error fetching price for product ${product.id}:`, err));
      }
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
        category: "",
      };
      const response = await api.post("/products", payload);
      alert(`Product tracking started for: ${response.data.name}`);
      setUrl("");
      await fetchProducts();
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

  return (
    <div className="container mx-auto p-4">
      <div className="w-full max-w-md mx-auto flex flex-col gap-4 mb-8">
        <h2 className="text-2xl font-bold text-center text-white">Track a New Product</h2>
        <input
          type="text"
          placeholder="Enter product URL to track"
          className="p-3 border border-gray-300 bg-gray-100 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button
          onClick={handleTrackProduct}
          disabled={isTracking}
          className={`bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 transition ${isTracking ? "opacity-50 cursor-not-allowed" : ""}`}>
          {isTracking ? "Tracking..." : "Track Product"}
        </button>
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-4 text-white">Your Tracked Products</h2>
        {isProductsLoading && <p>Loading products...</p>}
        {error && <p className="text-red-500">{error}</p>}
        {!isProductsLoading && !error && products.length === 0 && <p>You are not tracking any products yet.</p>}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.map(product => (
            <Link to={`/products/${product.id}`} key={product.id} className="bg-purple-950 p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow block border-2 border-gray-400">
              <h3 className="font-bold text-lg truncate text-gray-300" title={product.name}>{product.name}</h3>
              {prices[product.id] !== undefined && (
                <p className="text-green-500 font-bold mt-2">Price: {prices[product.id]}</p>
              )}
              <p className="text-gray-400 text-sm break-all">{getDomain(product.url)}</p>
              <p className="text-gray-400 text-xs mt-2">Tracked since: {new Date(product.created_at).toLocaleDateString()}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

export default HomePage;