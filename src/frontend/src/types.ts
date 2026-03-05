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
}