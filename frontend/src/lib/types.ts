export interface PaymentQr {
  qr_data_url: string | null;
  updated_at: string | null;
}

export interface AdminLoginResponse {
  authenticated: boolean;
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