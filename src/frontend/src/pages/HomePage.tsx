import { useState, useEffect } from "react";
import api from "../api/client";
import { showAlert } from "../utils/alerts";
import type { Product, Tracking, ScrapedItem, ScrapeResult } from "../types";

import SearchSection from "../components/SearchSection";
import CandidateSelection from "../components/CandidateSelection";
import Dashboard from "../components/Dashboard";

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
  const [view, setView] = useState<"home" | "selection">("home");
  const [candidates, setCandidates] = useState<ScrapedItem[]>([]);
  const [selectedUrls, setSelectedUrls] = useState<Set<string>>(new Set());

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
    if (error) {
      const timer = setTimeout(() => {
        setError(null);
      }, 10000);
      return () => clearTimeout(timer);
    }
  }, [error]);

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
          if (err.response?.status !== 404) {
            console.error(`Error fetching price for product ${product.id}:`, err);
          }
        });
    });
  }, [products]);

  const isUrl = (str: string) => {
    try {
      const parsed = new URL(str);
      return parsed.protocol === "http:" || parsed.protocol === "https:";
    } catch {
      return false;
    }
  };

  const handleTrackProduct = async () => {
    const input = url.trim();
    if (!input) {
      showAlert("Please enter a URL or product name.");
      return;
    }

    setIsTracking(true);
    setError(null);
    try {
      if (isUrl(input)) {
        const scrapeRes = await api.post<ScrapeResult>("/scrape/url", { url: input });
        const scrapedProduct = scrapeRes.data;

        showAlert(`Product tracking started for: ${scrapedProduct.name}`);
        setUrl("");
        await fetchData();
      } else {
        const response = await api.post<ScrapeResult>("/scrape/category", {
          category: category,
          name: input,
          limit: 10,
        });

        if (response.data.data && response.data.data.length > 0) {
          setCandidates(response.data.data);
          setSelectedUrls(new Set());
          setView("selection");
        } else {
          showAlert("No products found for this search.");
        }
      }
    } catch (err: any) {
      console.error("Error in scraping flow:", err);
      const rawDetail = err.response?.data?.detail;
      const detail = typeof rawDetail === "string"
        ? rawDetail
        : (rawDetail ? JSON.stringify(rawDetail.message) : "Scrape failed.");
      setError(detail);
      showAlert(`Error: ${detail}`);
    } finally {
      setIsTracking(false);
    }
  };

  const handleTrackSelected = async () => {
    if (selectedUrls.size === 0) {
      showAlert("Please select at least one item to track.");
      return;
    }

    setIsTracking(true);
    try {
      const selectedItems = candidates.filter((c) => selectedUrls.has(c.url));
      const items = selectedItems.map((item) => ({
        name: item.name,
        url: item.url,
        category: category,
        price: item.price,
        source: item.source,
        image_url: item.image_url,
      }));

      await api.post("/products/bulk", { items });

      showAlert(`Successfully tracked ${selectedUrls.size} items.`);
      setView("home");
      setUrl("");
      await fetchData();
    } catch (err: any) {
      console.error("Error tracking selected items:", err);
      const rawDetail = err.response?.data?.detail;
      const detail = typeof rawDetail === "string" 
        ? rawDetail 
        : (rawDetail ? JSON.stringify(rawDetail.message) : "Failed to track items.");
      showAlert(`Error: ${detail}`);
    } finally {
      setIsTracking(false);
    }
  };

  const toggleCandidate = (candidateUrl: string) => {
    setSelectedUrls((prev) => {
      const next = new Set(prev);
      if (next.has(candidateUrl)) next.delete(candidateUrl);
      else next.add(candidateUrl);
      return next;
    });
  };

  const toggleTracking = async (e: React.MouseEvent, trackingId: number) => {
    e.preventDefault();
    try {
      await api.patch(`/tracking/${trackingId}/active`, {});
      setTrackings((prev) =>
        prev.map((t) =>
          t.id === trackingId ? { ...t, is_active: !t.is_active } : t,
        )
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

  const combined = products
    .map((p) => {
      const t = trackings.find((tr) => tr.product_id === p.id);
      return { ...p, tracking: t };
    })
    .filter((item) => item.tracking);

  const activeProducts = combined.filter((p) => p.tracking?.is_active);
  const inactiveProducts = combined.filter((p) => !p.tracking?.is_active);

  if (view === "selection") {
    return (
      <CandidateSelection
        candidates={candidates}
        selectedUrls={selectedUrls}
        onToggleCandidate={toggleCandidate}
        onTrackSelected={handleTrackSelected}
        onBack={() => setView("home")}
        isTracking={isTracking}
      />
    );
  }

  return (
    <div className="container mx-auto p-4 min-h-screen">
      <SearchSection
        url={url}
        setUrl={setUrl}
        category={category}
        setCategory={setCategory}
        handleTrackProduct={handleTrackProduct}
        isTracking={isTracking}
      />

      <Dashboard
        isLoading={isProductsLoading}
        error={error}
        products={products}
        activeProducts={activeProducts}
        inactiveProducts={inactiveProducts}
        prices={prices}
        refreshing={refreshing}
        onRefreshPrice={refreshPrice}
        onToggleTracking={toggleTracking}
        onDeleteTracking={deleteTracking}
      />
    </div>
  );
}

export default HomePage;

