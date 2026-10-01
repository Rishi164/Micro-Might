# Micro Might living spec

## Product
Multipage premium farm-to-table storefront for Micro Might, a Bengaluru microgreens brand based in Gottigere. The primary conversion is a persistent cart and stored checkout order. WhatsApp is reserved for enquiries, custom-variety requests, payment help and customer support. Customer-facing messaging says “freshly grown, handled with care, and brought to doorsteps across Bengaluru” and does not use “local” or “locally.”

## Routes
- `/` Home: brand story, featured varieties, G.Y.O.C. overview, reasons to choose Micro Might, serving ideas and shop CTAs
- `/microgreens` exact 14-variety catalog plus Signature Mix, regular/G.Y.O.C. pricing and add-to-cart controls
- `/gyoc` Grow Your Own Crop explanation, four-step journey, pricing context and custom request CTA
- `/ways-to-enjoy`, `/about`, `/contact`, `/payment`
- `/cart` persistent browser cart with quantity changes and removal
- `/checkout` guest-or-account checkout with QR/COD, distance estimate and stored order creation
- `/login` optional customer sign-in/account creation; `/account` customer order history
- `/admin` admin dashboard for orders, delivery-fee approval, confirmation/cancellation, payment QR management and additional admin creation

## Data model
- Product data is a static, hand-maintained TypeScript catalog with exact requested names, varieties and Regular/G.Y.O.C. prices.
- Backend `payment_qr` collection stores one `primary` QR data URL and UTC update timestamp.
- `users` stores PBKDF2-hashed customer/admin credentials; `sessions` stores expiring httpOnly cookie sessions.
- `orders` stores server-priced order items, customer/delivery details, payment method, fee estimate, admin-approved fee, totals, status and email-delivery state.
- Server-side catalog pricing is canonical; checkout prices from the browser are never trusted.
- `POST /api/orders` accepts guest or signed-in orders; `/api/orders/mine` is customer-owned; `/api/admin/orders*` requires an admin session.
- `GET /api/payment-qr` is public; `PUT /api/payment-qr` requires an admin session.

## Auth and admin
- Customer accounts are optional. Signup/login use email and password; authenticated orders appear in the customer dashboard. Guest checkout remains available.
- Auth uses secure, httpOnly, same-site cookie sessions. Passwords are PBKDF2 hashed and never returned.
- The seeded admin credentials are in `memory/test_credentials.md`. Signed-in admins can add additional admins with their own username, email and password.
- Admins approve the final delivery fee and confirm or cancel each order. That action updates the stored order and sends a status email.

## Transactional email
- Emergent-managed Resend sends fixed, server-side transactional templates only.
- Every stored order sends a new-order notification to `micromights@gmail.com` and an order-received message to the customer's stored order email.
- Admin confirmation/cancellation sends the customer a status email with the final approved total.
- Sender display name is Micro Might; Reply-To is `micromights@gmail.com`.

## Payment and delivery
- Customers choose the supplied PhonePe QR (payee shown as Rishi Vardhan G) or Cash on Delivery during checkout.
- Cash on Delivery carries an additional ₹30 charge.
- Delivery is free within 5 km of Gottigere. Beyond 5 km, checkout estimates ₹9 per additional km and an admin approves the final delivery fee.
- Business email: `micromights@gmail.com`.

## Accuracy constraints
Do not alter product names, variety names, prices, phone numbers, exact address, FSSAI number, WhatsApp number, delivery rates or COD charge. Do not add medical, organic, pesticide-free, chemical-free, testimonial, award or founder claims. WhatsApp is not an ordering channel.