import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, LogOut, PackageCheck } from "lucide-react";
import { PageIntro, SiteLayout } from "@/components/SiteShell";
import { apiGet } from "@/lib/api";
import { endSession, useSession } from "@/lib/session";
import type { Order } from "@/lib/types";

function statusLabel(status: Order["status"]) {
  return status === "pending_approval" ? "Awaiting approval" : status === "confirmed" ? "Confirmed" : "Cancelled";
}

export default function Account() {
  const navigate = useNavigate();
  const session = useSession();
  const user = session.data?.user;
  const ordersQuery = useQuery({ queryKey: ["my-orders"], queryFn: () => apiGet<Order[]>("/orders/mine"), enabled: Boolean(user?.role === "customer"), retry: false });

  if (session.isLoading) return <SiteLayout><section className="min-h-[50vh] bg-cream" /></SiteLayout>;
  if (!user || user.role !== "customer") return <SiteLayout><PageIntro eyebrow="Customer dashboard" title="Sign in to see your orders." description="Accounts are optional. You can always continue shopping and complete checkout as a guest." /><section className="bg-cream px-5 py-16 text-center"><Link to="/login" className="inline-flex items-center gap-2 rounded-full bg-forest px-6 py-4 text-xs font-bold uppercase tracking-[0.1em] text-white" data-testid="account-login-button">Sign in or create account <ArrowRight size={15} /></Link></section></SiteLayout>;

  return <SiteLayout><PageIntro eyebrow={`Welcome, ${user.name}`} title="Your Micro Might orders." description="See which orders are awaiting delivery-fee approval and which have been confirmed by the Micro Might team." /><section className="bg-cream px-5 py-14 sm:py-20 lg:px-10 lg:py-24" data-testid="account-section"><div className="mx-auto max-w-[1000px]"><div className="flex flex-col justify-between gap-4 border-b border-line pb-6 sm:flex-row sm:items-center"><div><p className="text-sm font-semibold text-forest" data-testid="account-email">{user.email}</p><p className="mt-1 text-xs text-ink/50">Customer account</p></div><button type="button" onClick={async () => { await endSession(); navigate("/"); }} className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[0.1em] text-forest" data-testid="customer-logout-button"><LogOut size={15} /> Sign out</button></div>{ordersQuery.data?.length ? <div className="mt-8 space-y-5">{ordersQuery.data.map((order) => <article key={order.id} className="rounded-2xl border border-line bg-white p-6 sm:p-8" data-testid={`account-order-${order.id}`}><div className="flex flex-col justify-between gap-4 sm:flex-row"><div><p className="label text-green">{order.order_number}</p><h2 className="mt-2 font-heading text-3xl text-forest">{statusLabel(order.status)}</h2><p className="mt-2 text-xs text-ink/50">Placed {new Date(order.created_at).toLocaleDateString("en-IN", { dateStyle: "medium" })}</p></div><div className="text-left sm:text-right"><p className="font-heading text-4xl text-forest">₹{order.total}</p><p className="text-xs text-ink/50">{order.approved_delivery_fee === null ? "Estimated total" : "Confirmed total"}</p></div></div><div className="mt-6 border-t border-line pt-5 text-sm text-ink/60">{order.items.map((item) => <p key={`${item.product_slug}-${item.plan}-${item.weight}`} className="mt-1">{item.name} · {item.weight} · {item.plan === "gyoc" ? "G.Y.O.C." : "Regular"} × {item.quantity}</p>)}</div></article>)}</div> : <div className="mt-8 rounded-2xl border border-line bg-white p-10 text-center" data-testid="account-empty-orders"><PackageCheck className="mx-auto text-green" size={30} /><h2 className="mt-4 font-heading text-4xl text-forest">No orders here yet.</h2><Link to="/microgreens" className="mt-6 inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[0.1em] text-green" data-testid="account-shop-link">Shop microgreens <ArrowRight size={14} /></Link></div>}</div></section></SiteLayout>;
}