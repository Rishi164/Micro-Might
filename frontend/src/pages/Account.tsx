import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, CalendarDays, CheckCircle2, Home, LogOut, PackageCheck, Sprout, Truck } from "lucide-react";
import { PageIntro, SiteLayout } from "@/components/SiteShell";
import { apiGet, apiPut } from "@/lib/api";
import { endSession, updateSessionUser, useSession } from "@/lib/session";
import type { Order, User } from "@/lib/types";

function statusLabel(status: Order["status"]) {
  return status === "pending_approval" ? "Awaiting approval" : status === "confirmed" ? "Confirmed" : "Cancelled";
}

function formatDate(value: string | null) {
  if (!value) return "Awaiting admin";
  return new Date(`${value}T00:00:00`).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

function AddressEditor({ user }: { user: User }) {
  const [form, setForm] = useState({ address: user.home_address ?? "", pincode: user.home_pincode ?? "", distance: String(user.home_distance_km ?? 0) });
  const mutation = useMutation({
    mutationFn: () => apiPut<User>("/auth/address", { home_address: form.address, home_pincode: form.pincode, home_distance_km: Number(form.distance) }),
    onSuccess: (updated) => updateSessionUser(updated),
  });

  return <section className="rounded-2xl border border-line bg-white p-6 sm:p-8" data-testid="customer-address-card"><div className="flex items-start gap-4"><span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-sage text-green"><Home size={20} /></span><div><p className="label text-green">Saved delivery details</p><h2 className="mt-2 font-heading text-3xl text-forest">Your home address</h2><p className="mt-2 text-sm text-ink/55">We’ll pre-fill this address at checkout. You can still change it for any order.</p></div></div><form className="mt-6 grid gap-4 sm:grid-cols-2" onSubmit={(event) => { event.preventDefault(); mutation.mutate(); }} data-testid="customer-address-form"><label className="text-xs font-bold uppercase tracking-[0.1em] text-green sm:col-span-2">Home address<textarea required minLength={12} rows={3} value={form.address} onChange={(event) => setForm({ ...form, address: event.target.value })} className="mt-2 w-full rounded-xl border border-line bg-cream px-4 py-3 text-sm normal-case tracking-normal text-ink" data-testid="customer-home-address-input" /></label><label className="text-xs font-bold uppercase tracking-[0.1em] text-green">Pincode<input required pattern="[0-9]{6}" value={form.pincode} onChange={(event) => setForm({ ...form, pincode: event.target.value })} className="mt-2 w-full rounded-xl border border-line bg-cream px-4 py-3 text-sm normal-case tracking-normal text-ink" data-testid="customer-home-pincode-input" /></label><label className="text-xs font-bold uppercase tracking-[0.1em] text-green">Distance from Gottigere (km)<input required type="number" min="0" max="100" step="0.1" value={form.distance} onChange={(event) => setForm({ ...form, distance: event.target.value })} className="mt-2 w-full rounded-xl border border-line bg-cream px-4 py-3 text-sm normal-case tracking-normal text-ink" data-testid="customer-home-distance-input" /></label>{mutation.isError && <p className="text-sm text-red-700 sm:col-span-2">Could not save this address. Please check the details.</p>}<button type="submit" disabled={mutation.isPending} className="inline-flex items-center justify-center gap-2 rounded-full bg-forest px-5 py-3 text-xs font-bold uppercase tracking-[0.1em] text-white sm:col-span-2 sm:justify-self-start" data-testid="customer-save-address-button">{mutation.isSuccess ? <><CheckCircle2 size={15} /> Address saved</> : "Save home address"}</button></form></section>;
}

function OrderTimeline({ order }: { order: Order }) {
  const steps = [
    { label: "Requested", value: formatDate(order.preferred_delivery_date), icon: CalendarDays },
    { label: "Harvest", value: formatDate(order.approved_harvest_date), icon: Sprout },
    { label: "Delivery", value: formatDate(order.approved_delivery_date), icon: Truck },
  ];
  return <div className="mt-6 grid gap-3 sm:grid-cols-3" data-testid={`order-timeline-${order.id}`}>{steps.map((step, index) => <div key={step.label} className={`rounded-xl p-4 ${index === 0 || order.status === "confirmed" ? "bg-sage" : "border border-dashed border-line"}`} data-testid={`order-timeline-${step.label.toLowerCase()}-${order.id}`}><step.icon size={17} className="text-green" /><p className="mt-3 text-[10px] font-bold uppercase tracking-[0.12em] text-green">{step.label}</p><p className="mt-1 text-sm font-semibold text-forest">{step.value}</p></div>)}</div>;
}

export default function Account() {
  const navigate = useNavigate();
  const session = useSession();
  const user = session.data?.user;
  const ordersQuery = useQuery({ queryKey: ["my-orders"], queryFn: () => apiGet<Order[]>("/orders/mine"), enabled: Boolean(user?.role === "customer"), retry: false });

  if (session.isLoading) return <SiteLayout><section className="min-h-[50vh] bg-cream" /></SiteLayout>;
  if (!user || user.role !== "customer") return <SiteLayout><PageIntro eyebrow="Customer dashboard" title="Sign in to see your orders." description="Accounts are optional. You can always continue shopping and complete checkout as a guest." /><section className="bg-cream px-5 py-16 text-center"><Link to="/login" className="inline-flex items-center gap-2 rounded-full bg-forest px-6 py-4 text-xs font-bold uppercase tracking-[0.1em] text-white" data-testid="account-login-button">Sign in or create account <ArrowRight size={15} /></Link></section></SiteLayout>;

  return <SiteLayout><PageIntro eyebrow={`Welcome, ${user.name}`} title="Your Micro Might dashboard." description="Save your home address, follow requested and approved dates, and see every confirmed order in one place." /><section className="bg-cream px-5 py-14 sm:py-20 lg:px-10 lg:py-24" data-testid="account-section"><div className="mx-auto max-w-[1000px]"><div className="flex flex-col justify-between gap-4 border-b border-line pb-6 sm:flex-row sm:items-center"><div><p className="text-sm font-semibold text-forest" data-testid="account-email">{user.email}</p><p className="mt-1 text-xs text-ink/50">Customer account</p></div><button type="button" onClick={async () => { await endSession(); navigate("/"); }} className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[0.1em] text-forest" data-testid="customer-logout-button"><LogOut size={15} /> Sign out</button></div><div className="mt-8"><AddressEditor user={user} /></div>{ordersQuery.isLoading ? <div className="mt-10 rounded-2xl border border-line bg-white p-8 text-sm text-ink/55" data-testid="account-orders-loading">Loading your orders…</div> : ordersQuery.data?.length ? <div className="mt-10 space-y-5">{ordersQuery.data.map((order) => <article key={order.id} className="rounded-2xl border border-line bg-white p-6 sm:p-8" data-testid={`account-order-${order.id}`}><div className="flex flex-col justify-between gap-4 sm:flex-row"><div><p className="label text-green">{order.order_number}</p><h2 className="mt-2 font-heading text-3xl text-forest">{statusLabel(order.status)}</h2><p className="mt-2 text-xs text-ink/50">Placed {new Date(order.created_at).toLocaleDateString("en-IN", { dateStyle: "medium" })}</p></div><div className="text-left sm:text-right"><p className="font-heading text-4xl text-forest">₹{order.total}</p><p className="text-xs text-ink/50">{order.approved_delivery_fee === null ? "Estimated total" : "Confirmed total"}</p></div></div><OrderTimeline order={order} /><div className="mt-6 border-t border-line pt-5 text-sm text-ink/60">{order.items.map((item) => <p key={`${item.product_slug}-${item.plan}-${item.weight}`} className="mt-1">{item.name} · {item.weight} · {item.plan === "gyoc" ? "G.Y.O.C." : "Regular"} × {item.quantity}</p>)}</div><p className="mt-4 text-xs text-ink/50" data-testid={`account-order-address-${order.id}`}>Deliver to: {order.delivery_address}, {order.pincode}</p></article>)}</div> : <div className="mt-10 rounded-2xl border border-line bg-white p-10 text-center" data-testid="account-empty-orders"><PackageCheck className="mx-auto text-green" size={30} /><h2 className="mt-4 font-heading text-4xl text-forest">No orders here yet.</h2><Link to="/microgreens" className="mt-6 inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[0.1em] text-green" data-testid="account-shop-link">Shop microgreens <ArrowRight size={14} /></Link></div>}</div></section></SiteLayout>;
}