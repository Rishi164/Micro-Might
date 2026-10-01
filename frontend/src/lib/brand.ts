export const WHATSAPP_NUMBER = "919482428467";
export const WHATSAPP_DISPLAY = "9482428467";
export const PHONE_NUMBER = "9901693851";
export const EMAIL = "micromights@gmail.com";
export const ADDRESS = "#280, 5th Cross, Weaver’s Colony, BG Road, Gottigere, Bengaluru – 560083";
export const DIRECTIONS_URL = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(ADDRESS)}`;
export const LOGO_URL = "https://customer-assets-4nw71qhi.emergentagent.net/job_fresh-from-trays/artifacts/ie8zyhiz_LOGO.jpeg";
export const PAYMENT_QR_URL = "https://customer-assets-4nw71qhi.emergentagent.net/job_fresh-from-trays/artifacts/zncy8do5_image.png";

export function whatsappUrl(message: string) {
  return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;
}

export const customVarietyUrl = whatsappUrl(
  "Hi Micro Might, I'd like to request a custom microgreen variety through G.Y.O.C. The variety I'm looking for is ______.",
);

export const paymentProofUrl = whatsappUrl(
  "Hi Micro Might, I've completed my payment. I'm sharing the payment proof and my order details here.",
);
