# Micro Might living spec

## Product
Multipage premium farm-to-table website for Micro Might, a local microgreens brand in Gottigere, Bengaluru. The primary conversion is a pre-filled WhatsApp order; there is no cart, customer account, inventory system, or payment gateway.

## Routes
- `/` Home: brand story, featured varieties, G.Y.O.C. overview, reasons to choose Micro Might, serving ideas, WhatsApp CTAs
- `/microgreens` exact 14-variety catalog plus Signature Mix, regular/G.Y.O.C. pricing and product-specific WhatsApp ordering
- `/gyoc` Grow Your Own Crop explanation, four-step journey, pricing context and custom request CTA
- `/ways-to-enjoy`, `/about`, `/contact`, `/payment`
- `/admin` demo admin dashboard for replacing the payment QR image. The supplied PhonePe QR is the default public QR.

## Data model
- Product data is a static, hand-maintained TypeScript catalog with exact requested names, varieties and Regular/G.Y.O.C. prices.
- Backend `payment_qr` collection stores one `primary` QR data URL and UTC update timestamp.
- `GET /api/payment-qr` is public for the payment page.
- `PUT /api/payment-qr` validates the demo credentials and replaces the QR image.

## Auth and admin
The admin page uses a clearly labelled demo login. Credentials are in `memory/test_credentials.md` and `backend/.env`. This is demo authentication, not production identity management. Customers send payment proof on WhatsApp; payment verification is manual.

## Payment and delivery
- Customers may pay with the supplied PhonePe QR (payee shown as Rishi Vardhan G), contact Micro Might for help, or request Cash on Delivery.
- Cash on Delivery carries an additional ₹30 charge.
- Delivery is free within 5 km of Gottigere. Beyond 5 km, delivery is ₹9 per km across Bengaluru.
- Business email: `micromights@gmail.com`.

## Accuracy constraints
Do not alter product names, variety names, prices, phone numbers, exact address, FSSAI number, WhatsApp number, delivery rates or COD charge. Do not add medical, organic, pesticide-free, chemical-free, testimonial, award or founder claims.