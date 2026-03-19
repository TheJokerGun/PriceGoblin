export interface Product {
  id: number;
  name: string | null;
  url: string | null;
  category: string | null;
  image_url: string | null;
  tracking_id: number | null;
  is_active: boolean | null;
  source: string | null;
  target_price: number | null;
  created_at: string;
}

export interface Price {
  id: number;
  price: number;
  checked_at: string;
}
