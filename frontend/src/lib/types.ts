export interface PaymentQr {
  qr_data_url: string | null;
  updated_at: string | null;
}

export interface AdminLoginResponse {
  authenticated: boolean;
  user: User;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: "customer" | "admin";
  username: string | null;
  phone: string | null;
  home_address: string | null;
  home_pincode: string | null;
  home_distance_km: number | null;
  created_at: string;
}

export interface AuthResponse {
  authenticated: boolean;
  user: User;
}

export interface SessionState {
  user: User | null;
}

export interface OrderItem {
  product_slug: string;
  name: string;
  variety: string;
  plan: "regular" | "gyoc";
  weight: "50g" | "100g";
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface Order {
  id: string;
  order_number: string;
  customer_id: string | null;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  delivery_address: string;
  pincode: string;
  estimated_distance_km: number;
  preferred_delivery_date: string | null;
  approved_harvest_date: string | null;
  approved_delivery_date: string | null;
  payment_method: "qr" | "cod";
  payment_reference: string | null;
  payment_status: string;
  status: "pending_approval" | "confirmed" | "cancelled";
  items: OrderItem[];
  subtotal: number;
  cod_fee: number;
  estimated_delivery_fee: number;
  approved_delivery_fee: number | null;
  total: number;
  notes: string | null;
  email_status: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface InventoryItem {
  product_slug: string;
  name: string;
  variety: string;
  tracking_enabled: boolean;
  stock_50g: number;
  stock_100g: number;
  updated_at: string | null;
}

export interface ProductPrice {
  small: number;
  large: number;
}

export interface MicrogreenProduct {
  slug: string;
  name: string;
  variety: string;
  description: string;
  regular: ProductPrice;
  gyoc: ProductPrice;
  image: string;
}

export interface EnjoymentIdea {
  title: string;
  description: string;
  image: string;
}