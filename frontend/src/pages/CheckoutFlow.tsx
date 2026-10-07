import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowRight, Banknote, CheckCircle2, CreditCard, Mail, ShoppingBag } from "lucide-react";
import { PageIntro, SiteLayout } from "@/components/SiteShell";
import { useCart } from "@/components/CartProvider";
import { apiGet, apiPost, ApiError } from "@/lib/api";
import { useSession } from "@/lib/session";
import type { Order, OrderCreateRequest, RazorpayConfig, RazorpayOrder, RazorpayPaymentResult } from "@/lib/types";

interface RazorpayOptions {
  key: string;
  amount: number;
  currency: "INR";
  name: string;
  description: string;
  order_id: string;
  prefill: { name: string; email: string; contact: string };
  theme: { color: string };
  modal: { ondismiss: () => void };
  handler: (payment: RazorpayPaymentResult) => void;
}

declare global {
  interface Window {
    Razorpay?: new (options: RazorpayOptions) => { open: () => void };
  }
}

function loadRazorpayScript() {
  return new Promise<void>((resolve, reject) => {
    if (window.Razorpay) return resolve();
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => window.Razorpay ? resolve() : reject(new Error("Razorpay Checkout did not load."));
    script.onerror = () => reject(new Error("Could not load Razorpay Checkout. Check your connection and try again."));
    document.body.appendChild(script);
  });
}

function errorMessage(error: unknown) {
  if (error instanceof ApiError && typeof error.body === "object" && error.body !== null && "detail" in error.body) {
    const detail = error.body.detail;
    if (typeof detail === "string") return detail;
  }
  return error instanceof Error ? error.message : "We could not complete checkout. Please try again.";
}

export default function CheckoutFlow() {
  const { items, subtotal, clearCart } = useCart();
  const queryClient = useQueryClient();
  const session = useSession();
  const user = session.data?.user;
  const paymentConfig = useQuery({
    queryKey: ["razorpay-config"],
    queryFn: () => apiGet<RazorpayConfig>("/payments/razorpay/config"),
    retry: false,
  });
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    address: "",
    pincode: "",
    distance: "0",
    preferredDate: "",
    saveAddress: true,
    payment: "razorpay" as "razorpay" | "cod",
    notes: "",
  });
  const [completedOrder, setCompletedOrder] = useState<Order | null>(null);
  const [paymentError, setPaymentError] = useState("");

  useEffect(() => {
    if (!user) return;
    setForm((current) => ({
      ...current,
      name: current.name || user.name,
      email: current.email || user.email,
      phone: current.phone || user.phone || "",
      address: current.address || user.home_address || "",
      pincode: current.pincode || user.home_pincode || "",
      distance: current.distance !== "0" ? current.distance : String(user.home_distance_km ?? 0),
    }));
  }, [user]);

  const bengaluruEligible = form.pincode.startsWith("560");
  const razorpayAvailable = paymentConfig.data?.enabled === true;
  const estimatedDeliveryFee = useMemo(() => Math.max(0, Math.ceil(Number(form.distance || 0) - 5)) * 9, [form.distance]);
  const codFee = form.payment === "cod" ? 30 : 0;
  const estimatedTotal = subtotal + estimatedDeliveryFee + codFee;

  useEffect(() => {
    if (!paymentConfig.isLoading && !razorpayAvailable && bengaluruEligible && form.payment === "razorpay") {
      setForm((current) => ({ ...current, payment: "cod" }));
    }
    if (!bengaluruEligible && form.payment === "cod") {
      setForm((current) => ({ ...current, payment: "razorpay" }));
    }
  }, [bengaluruEligible, form.payment, paymentConfig.isLoading, razorpayAvailable]);

  function orderPayload(payment: OrderCreateRequest["payment_method"]): OrderCreateRequest {
    return {
      customer_name: form.name,
      customer_email: form.email,
      customer_phone: form.phone,
      delivery_address: form.address,
      pincode: form.pincode,
      estimated_distance_km: Number(form.distance),
      preferred_delivery_date: form.preferredDate,
      save_address: Boolean(user && form.saveAddress),
      payment_method: payment,
      payment_reference: null,
      notes: form.notes || null,
      items: items.map((item) => ({
        product_slug: item.productSlug,
        plan: item.plan,
        weight: item.weight,
        quantity: item.quantity,
      })),
    };
  }

  function finishOrder(order: Order) {
    setCompletedOrder(order);
    clearCart();
    void queryClient.invalidateQueries({ queryKey: ["my-orders"] });
    void queryClient.invalidateQueries({ queryKey: ["auth-session"] });
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }

  const verifyPayment = useMutation({
    mutationFn: (payment: RazorpayPaymentResult) => apiPost<Order>("/payments/razorpay/verify", payment),
    onSuccess: finishOrder,
    onError: (error) => setPaymentError(errorMessage(error)),
  });

  const createRazorpayOrder = useMutation({
    mutationFn: () => apiPost<RazorpayOrder>("/payments/razorpay/order", orderPayload("razorpay")),
    onSuccess: async (gatewayOrder) => {
      try {
        await loadRazorpayScript();
        if (!window.Razorpay) throw new Error("Razorpay Checkout is unavailable in this browser.");
        new window.Razorpay({
          key: gatewayOrder.key_id,
          amount: gatewayOrder.amount,
          currency: gatewayOrder.currency,
          name: "Micro Might",
          description: "Fresh microgreens order",
          order_id: gatewayOrder.order_id,
          prefill: { name: form.name, email: form.email, contact: form.phone },
          theme: { color: "#143621" },
          modal: { ondismiss: () => setPaymentError("Payment was not completed. Your order has not been placed.") },
          handler: (payment) => verifyPayment.mutate(payment),
        }).open();
      } catch (error) {
        setPaymentError(errorMessage(error));
      }
    },
    onError: (error) => setPaymentError(errorMessage(error)),
  });

  const placeCodOrder = useMutation({
    mutationFn: () => apiPost<Order>("/orders", orderPayload("cod")),
    onSuccess: finishOrder,
    onError: (error) => setPaymentError(errorMessage(error)),
  });

  function update(key: keyof typeof form, value: string | boolean) {
    setForm((current) => ({ ...current, [key]: value }));
    setPaymentError("");
  }

  const isSubmitting = createRazorpayOrder.isPending || verifyPayment.isPending || placeCodOrder.isPending;
  const canSubmit = form.payment === "cod" ? bengaluruEligible : razorpayAvailable && !paymentConfig.isLoading;

  if (completedOrder) return <SiteLayout><section className="bg-cream px-5 py-20 lg:px-10 lg:py-32" data-testid="order-success"><div className="mx-auto max-w-2xl rounded-[2rem] border border-line bg-white p-8 text-center shadow-[0_15px_45px_rgba(0,0,0,0.05)] sm:p-14"><CheckCircle2 className="mx-auto text-green" size={44} /><p className="label mt-6 text-green">Order received</p><h1 className="mt-3 font-heading text-5xl text-forest" data-testid="order-success-title">Thank you, {completedOrder.customer_name}.</h1><p className="mt-5 text-base leading-relaxed text-ink/60">Your order <strong data-testid="order-success-number">{completedOrder.order_number}</strong> is stored and awaiting admin approval of the delivery fee. We sent the order details to {completedOrder.customer_email} and notified Micro Might.</p><div className="mt-7 rounded-xl bg-sage p-5 text-left"><div className="flex justify-between text-sm"><span>Estimated total</span><strong className="text-forest" data-testid="order-success-total">₹{completedOrder.total}</strong></div><p className="mt-2 text-xs text-ink/50">Payment: {completedOrder.payment_method === "cod" ? "Cash on Delivery" : "Razorpay paid"}. Your final delivery fee is confirmed by email.</p></div><div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">{user && <Link to="/account" className="rounded-full bg-forest px-6 py-4 text-xs font-bold uppercase tracking-[0.1em] text-white" data-testid="success-account-link">View my orders</Link>}<Link to="/microgreens" className="rounded-full border border-forest px-6 py-4 text-xs font-bold uppercase tracking-[0.1em] text-forest" data-testid="success-shop-link">Continue shopping</Link></div></div></section></SiteLayout>;

  if (items.length === 0) return <SiteLayout><PageIntro eyebrow="Checkout" title="Your cart is empty." description="Choose your microgreens first, then return here to complete your order." /><section className="bg-cream px-5 py-16 text-center"><Link to="/microgreens" className="inline-flex items-center gap-2 rounded-full bg-forest px-6 py-4 text-xs font-bold uppercase tracking-[0.1em] text-white" data-testid="checkout-empty-shop-button">Shop microgreens <ArrowRight size={15} /></Link></section></SiteLayout>;

  return <SiteLayout><PageIntro eyebrow="Secure checkout" title="Tell us where the freshness is going." description="Checkout as a guest or sign in to use your saved home address. Choose when you need the order; Micro Might reviews stock, fees and final dates." /><section className="bg-cream px-5 py-14 sm:py-20 lg:px-10 lg:py-24" data-testid="checkout-section"><form className="mx-auto grid max-w-[1180px] gap-8 lg:grid-cols-[1.1fr_0.9fr]" onSubmit={(event) => { event.preventDefault(); setPaymentError(""); if (form.payment === "cod") placeCodOrder.mutate(); else createRazorpayOrder.mutate(); }} data-testid="checkout-form"><div className="space-y-6"><div className="rounded-2xl border border-line bg-white p-6 sm:p-8"><div className="flex items-center justify-between gap-4"><div><p className="label text-green">Contact details</p><h2 className="mt-2 font-heading text-3xl text-forest">Who is placing this order?</h2></div>{!user && <Link to="/login" className="text-xs font-bold uppercase tracking-[0.1em] text-green" data-testid="checkout-login-link">Sign in</Link>}</div><div className="mt-6 grid gap-4 sm:grid-cols-2"><label className="text-xs font-bold uppercase tracking-[0.1em] text-green">Full name<input required minLength={2} value={form.name} onChange={(event) => update("name", event.target.value)} autoComplete="name" className="mt-2 w-full rounded-xl border border-line bg-cream px-4 py-3 text-sm normal-case tracking-normal text-ink outline-none focus:border-green" data-testid="checkout-name-input" /></label><label className="text-xs font-bold uppercase tracking-[0.1em] text-green">Email<input required type="email" value={form.email} onChange={(event) => update("email", event.target.value)} autoComplete="email" className="mt-2 w-full rounded-xl border border-line bg-cream px-4 py-3 text-sm normal-case tracking-normal text-ink outline-none focus:border-green" data-testid="checkout-email-input" /></label><label className="text-xs font-bold uppercase tracking-[0.1em] text-green sm:col-span-2">Phone<input required inputMode="tel" minLength={10} maxLength={15} value={form.phone} onChange={(event) => update("phone", event.target.value)} autoComplete="tel" className="mt-2 w-full rounded-xl border border-line bg-cream px-4 py-3 text-sm normal-case tracking-normal text-ink outline-none focus:border-green" data-testid="checkout-phone-input" /></label></div></div><div className="rounded-2xl border border-line bg-white p-6 sm:p-8"><p className="label text-green">Delivery</p><h2 className="mt-2 font-heading text-3xl text-forest">Where and when should we deliver?</h2><div className="mt-6 grid gap-4 sm:grid-cols-2"><label className="text-xs font-bold uppercase tracking-[0.1em] text-green sm:col-span-2">Home address<textarea required minLength={12} value={form.address} onChange={(event) => update("address", event.target.value)} rows={4} autoComplete="street-address" className="mt-2 w-full rounded-xl border border-line bg-cream px-4 py-3 text-sm normal-case tracking-normal text-ink outline-none focus:border-green" data-testid="checkout-address-input" /></label><label className="text-xs font-bold uppercase tracking-[0.1em] text-green">Pincode<input required inputMode="numeric" pattern="[0-9]{6}" value={form.pincode} onChange={(event) => update("pincode", event.target.value)} autoComplete="postal-code" className="mt-2 w-full rounded-xl border border-line bg-cream px-4 py-3 text-sm normal-case tracking-normal text-ink outline-none focus:border-green" data-testid="checkout-pincode-input" /></label><label className="text-xs font-bold uppercase tracking-[0.1em] text-green">Approx. distance from Gottigere (km)<input required type="number" min="0" max="100" step="0.1" value={form.distance} onChange={(event) => update("distance", event.target.value)} className="mt-2 w-full rounded-xl border border-line bg-cream px-4 py-3 text-sm normal-case tracking-normal text-ink outline-none focus:border-green" data-testid="checkout-distance-input" /></label><label className="text-xs font-bold uppercase tracking-[0.1em] text-green sm:col-span-2">When do you need it?<input required type="date" value={form.preferredDate} onChange={(event) => update("preferredDate", event.target.value)} className="mt-2 w-full rounded-xl border border-line bg-cream px-4 py-3 text-sm normal-case tracking-normal text-ink outline-none focus:border-green" data-testid="checkout-preferred-date-input" /></label></div>{user && <label className="mt-4 flex items-center gap-3 text-sm font-semibold text-forest"><input type="checkbox" checked={form.saveAddress} onChange={(event) => update("saveAddress", event.target.checked)} className="h-4 w-4 accent-[#143621]" data-testid="checkout-save-address-checkbox" /> Save this as my home address</label>}<p className="mt-4 text-xs leading-relaxed text-ink/50" data-testid="delivery-approval-note">Free within 5 km. Beyond 5 km, the estimate is ₹9 per additional km. An admin checks stock and approves the final fee and delivery date.</p></div><div className="rounded-2xl border border-line bg-white p-6 sm:p-8"><p className="label text-green">Payment method</p><div className="mt-5 grid gap-3 sm:grid-cols-2"><button type="button" onClick={() => update("payment", "razorpay")} disabled={!razorpayAvailable} className={`rounded-xl border p-5 text-left disabled:cursor-not-allowed disabled:opacity-50 ${form.payment === "razorpay" ? "border-forest bg-sage" : "border-line"}`} aria-pressed={form.payment === "razorpay"} data-testid="checkout-payment-razorpay"><CreditCard size={20} className="text-green" /><p className="mt-3 font-heading text-2xl text-forest">Razorpay</p><p className="mt-1 text-xs text-ink/50">Cards, UPI and net banking.</p></button><button type="button" onClick={() => update("payment", "cod")} disabled={!bengaluruEligible} className={`rounded-xl border p-5 text-left disabled:cursor-not-allowed disabled:opacity-50 ${form.payment === "cod" ? "border-forest bg-sage" : "border-line"}`} aria-pressed={form.payment === "cod"} data-testid="checkout-payment-cod"><Banknote size={20} className="text-green" /><p className="mt-3 font-heading text-2xl text-forest">Cash on Delivery</p><p className="mt-1 text-xs text-ink/50">Additional ₹30 · Bengaluru only.</p></button></div>{!razorpayAvailable && <p className="mt-4 rounded-lg bg-cream p-3 text-xs leading-relaxed text-ink/60" data-testid="razorpay-unavailable">Online payment is being set up. Enter a Bengaluru pincode beginning with 560 to use Cash on Delivery, or contact us for help.</p>}{!bengaluruEligible && <p className="mt-4 text-xs text-ink/55" data-testid="cod-area-note">Cash on Delivery is available only for Bengaluru pincodes beginning with 560.</p>}<label className="mt-5 block text-xs font-bold uppercase tracking-[0.1em] text-green">Order notes (optional)<textarea value={form.notes} onChange={(event) => update("notes", event.target.value)} rows={3} maxLength={500} className="mt-2 w-full rounded-xl border border-line bg-cream px-4 py-3 text-sm normal-case tracking-normal text-ink outline-none focus:border-green" data-testid="checkout-notes-input" /></label></div></div><aside className="h-fit rounded-2xl bg-forest p-6 text-cream lg:sticky lg:top-28 sm:p-8" data-testid="checkout-summary"><p className="label text-lime">Your order</p><div className="mt-6 space-y-4">{items.map((item) => <div key={item.key} className="flex justify-between gap-4 border-b border-white/10 pb-4 text-sm" data-testid={`checkout-summary-item-${item.key}`}><div><p className="font-semibold">{item.name}</p><p className="text-xs text-cream/55">{item.weight} · {item.plan === "gyoc" ? "G.Y.O.C." : "Regular"} · Qty {item.quantity}</p></div><span>₹{item.unitPrice * item.quantity}</span></div>)}</div><div className="mt-6 space-y-3 text-sm"><div className="flex justify-between text-cream/65"><span>Subtotal</span><span>₹{subtotal}</span></div><div className="flex justify-between text-cream/65"><span>Estimated delivery</span><span data-testid="checkout-delivery-fee">₹{estimatedDeliveryFee}</span></div><div className="flex justify-between text-cream/65"><span>COD fee</span><span>₹{codFee}</span></div><div className="flex justify-between border-t border-white/15 pt-4 font-heading text-3xl"><span>Estimate</span><span data-testid="checkout-total">₹{estimatedTotal}</span></div></div>{paymentError && <p className="mt-5 rounded-lg bg-red-950/40 p-3 text-xs text-red-100" role="alert" data-testid="checkout-error">{paymentError}</p>}<button type="submit" disabled={isSubmitting || !canSubmit} className="mt-7 inline-flex w-full items-center justify-center gap-2 rounded-full bg-lime px-6 py-4 text-xs font-bold uppercase tracking-[0.1em] text-forest disabled:opacity-50" data-testid="checkout-submit-button">{isSubmitting ? "Processing payment..." : <><ShoppingBag size={15} /> {form.payment === "cod" ? "Place COD order" : "Continue to payment"} <ArrowRight size={15} /></>}</button><div className="mt-5 flex items-start gap-2 text-xs leading-relaxed text-cream/55"><Mail size={14} className="mt-0.5 shrink-0" /> Both you and Micro Might receive the order by email. Final dates follow after admin review.</div></aside></form></section></SiteLayout>;
}