export interface Product {
  id: number;
  name: string;
  url: string;
  category: string | null;
  created_at: string;
}

export interface Price {
  id: number;
  price: number;
  checked_at: string;
}

export interface Tracking {
  id: number;
  product_id: number;
  is_active: boolean;
  target_price: number | null;
}

export interface ScrapedItem {
  name: string;
  price: number | string;
  source: string;
  url: string;
}

export interface ScrapeResult {
  type: "product" | "category";
  data?: ScrapedItem[];
  // If it's a single product result from /scrape/url
  id?: number;
  name?: string;
  url?: string;
  price?: number | string;
  category?: string | null;
  created_at?: string;
}