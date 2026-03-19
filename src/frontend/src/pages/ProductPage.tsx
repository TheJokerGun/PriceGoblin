import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import api from "../api/client";
import type { Price, Product } from "../types";
import { readLocalStorageJson, writeLocalStorageJson } from "../utils/storage";

const PRODUCT_CACHE_DURATION_MS = 60 * 60 * 1000;

type ProductPageCache = {
  product: Product;
  prices: Price[];
  timestamp: number;
};

const ProductPage = () => {
  const [searchParams] = useSearchParams();
  const id = searchParams.get("id");
  const [product, setProduct] = useState<Product | null>(null);
  const [prices, setPrices] = useState<Price[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    const fetchProductData = async () => {
      if (!id) {
        setError("Missing product id.");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      const cacheKey = `product_page_cache_${id}`;
      const cachedData = readLocalStorageJson<ProductPageCache | null>(
        cacheKey,
        null,
      );
      if (
        cachedData &&
        Date.now() - cachedData.timestamp < PRODUCT_CACHE_DURATION_MS
      ) {
        if (!isCancelled) {
          setProduct(cachedData.product);
          setPrices(cachedData.prices);
          setLoading(false);
        }
        return;
      }

      try {
        const [productResponse, pricesResponse] = await Promise.all([
          api.get<Product>(`/products/${id}`),
          api.get<Price[]>(`/products/${id}/prices`),
        ]);

        if (isCancelled) {
          return;
        }

        setProduct(productResponse.data);
        setPrices(pricesResponse.data);
        writeLocalStorageJson<ProductPageCache>(cacheKey, {
          product: productResponse.data,
          prices: pricesResponse.data,
          timestamp: Date.now(),
        });
      } catch (requestError) {
        console.error("Error fetching product data:", requestError);
        if (!isCancelled) {
          setError("Failed to fetch product data.");
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };

    void fetchProductData();

    return () => {
      isCancelled = true;
    };
  }, [id]);

  const formattedPrices = useMemo(
    () =>
      prices.map((priceEntry) => ({
        date: new Date(priceEntry.checked_at).toLocaleString(),
        price: Number(priceEntry.price),
      })),
    [prices],
  );

  if (loading) {
    return <div className="text-center text-white">Loading product details...</div>;
  }

  if (error) {
    return <div className="text-center text-red-500">{error}</div>;
  }

  if (!product) {
    return <div className="text-center text-white">Product not found.</div>;
  }

  return (
    <div className="container mx-auto p-4 text-white">
      <div className="mb-8">
        <Link to="/home" className="text-blue-400 hover:text-blue-300">
          &larr; Back to all products
        </Link>
      </div>
      <div className="bg-purple-950 p-8 rounded-lg shadow-lg border-2 border-gray-400">
        <h1 className="text-3xl font-bold mb-2 truncate" title={product.name ?? "Unknown product"}>
          {product.name ?? "Unknown product"}
        </h1>
        {product.url ? (
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-400 hover:underline break-all"
          >
            {product.url}
          </a>
        ) : (
          <p className="text-sm text-gray-400">No source URL saved for this product.</p>
        )}
        <p className="text-gray-400 text-xs mt-2">
          Tracked since: {new Date(product.created_at).toLocaleDateString()}
        </p>

        <div className="mt-8">
          <h2 className="text-2xl font-bold mb-4">Price History</h2>
          {prices.length > 1 ? (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={formattedPrices}>
                <CartesianGrid strokeDasharray="3 3" stroke="#4A5568" />
                <XAxis dataKey="date" stroke="#A0AEC0" />
                <YAxis
                  stroke="#A0AEC0"
                  domain={["dataMin - 25", "dataMax + 25"]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#2D3748",
                    border: "1px solid #4A5568",
                  }}
                  labelStyle={{ color: "#E2E8F0" }}
                />
                <Legend wrapperStyle={{ color: "#E2E8F0" }} />
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="#48BB78"
                  strokeWidth={2}
                  activeDot={{ r: 8 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p>Not enough price data to display a chart. Check back later.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductPage;
