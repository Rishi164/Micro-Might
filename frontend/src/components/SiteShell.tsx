import { useState, type ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import { ArrowRight, Menu, MessageCircle, ShoppingBag, UserRound, X } from "lucide-react";
import { ADDRESS, EMAIL, LOGO_URL, PHONE_NUMBER, WHATSAPP_DISPLAY, whatsappUrl } from "@/lib/brand";
import { useCart } from "@/components/CartProvider";
import { useSession } from "@/lib/session";

const navigation = [
  { label: "Home", to: "/" },
  { label: "Our Microgreens", to: "/microgreens" },
  { label: "G.Y.O.C.", to: "/gyoc" },
  { label: "Ways to Enjoy", to: "/ways-to-enjoy" },
  { label: "About", to: "/about" },
  { label: "Contact", to: "/contact" },
];

export function SiteHeader() {
  const [open, setOpen] = useState(false);
  const supportUrl = whatsappUrl("Hi Micro Might, I need help with your microgreens or my order.");
  const { itemCount } = useCart();
  const session = useSession();

  return (
    <>
      <div className="bg-forest px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-[0.18em] text-cream sm:text-xs" data-testid="delivery-strip">
        Free delivery within 5 km · ₹9/km beyond 5 km across Bengaluru
      </div>
      <header className="sticky top-0 z-50 border-b border-line/80 bg-cream/95 backdrop-blur-xl" data-testid="site-header">
        <div className="mx-auto flex max-w-[1380px] items-center justify-between px-5 py-4 lg:px-10">
          <Link to="/" className="group flex items-center gap-3" onClick={() => setOpen(false)} data-testid="brand-logo-link">
            <img src={LOGO_URL} alt="Micro Might logo" className="h-11 w-11 rounded-full border border-forest/15 object-cover shadow-[0_8px_20px_rgba(20,54,33,0.14)]" data-testid="brand-logo-image" />
            <span className="leading-none"><span className="block font-heading text-2xl font-semibold tracking-[-0.04em] text-forest">Micro Might</span><span className="mt-1 block text-[9px] font-bold uppercase tracking-[0.22em] text-green">Farm fresh greens</span></span>
          </Link>

          <nav className="hidden items-center gap-6 lg:flex" aria-label="Primary navigation" data-testid="desktop-navigation">
            {navigation.map((item) => (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => `relative py-2 text-[13px] font-semibold transition-colors duration-300 ${isActive ? "text-forest" : "text-ink/65 hover:text-forest"}`} data-testid={`nav-link-${item.label.toLowerCase().replaceAll(" ", "-").replaceAll(".", "")}`}>
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="hidden items-center gap-3 lg:flex">
            <Link to="/payment" className="px-3 py-2 text-[12px] font-bold uppercase tracking-[0.14em] text-forest hover:text-green" data-testid="payment-page-link">Pay securely</Link>
            <Link to={session.data?.user ? (session.data.user.role === "admin" ? "/admin" : "/account") : "/login"} className="grid h-10 w-10 place-items-center rounded-full border border-line text-forest" aria-label="Account" data-testid="header-account-link"><UserRound size={17} /></Link>
            <Link to="/cart" className="relative grid h-10 w-10 place-items-center rounded-full bg-forest text-white" aria-label={`Cart with ${itemCount} items`} data-testid="header-cart-link"><ShoppingBag size={17} />{itemCount > 0 && <span className="absolute -right-1 -top-1 grid h-5 min-w-5 place-items-center rounded-full bg-lime px-1 text-[10px] font-bold text-forest" data-testid="header-cart-count">{itemCount}</span>}</Link>
            <a href={supportUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-full bg-whatsapp px-5 py-3 text-[12px] font-bold uppercase tracking-[0.1em] text-white shadow-[0_10px_20px_rgba(37,211,102,0.16)] transition-transform duration-300 hover:-translate-y-1" data-testid="header-whatsapp-support-button"><MessageCircle size={15} /> WhatsApp support</a>
          </div>

          <button type="button" className="grid h-11 w-11 place-items-center rounded-full border border-line text-forest lg:hidden" onClick={() => setOpen((value) => !value)} aria-label={open ? "Close navigation" : "Open navigation"} aria-expanded={open} data-testid="mobile-menu-toggle">
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
        {open && <div className="border-t border-line bg-cream px-5 pb-5 pt-3 lg:hidden" data-testid="mobile-navigation">
          <nav className="flex flex-col gap-1" aria-label="Mobile navigation">
            {navigation.map((item) => <NavLink key={item.to} to={item.to} onClick={() => setOpen(false)} className="border-b border-line/70 py-3 font-heading text-xl text-forest" data-testid={`mobile-nav-link-${item.label.toLowerCase().replaceAll(" ", "-").replaceAll(".", "")}`}>{item.label}</NavLink>)}
          </nav>
          <div className="mt-4 flex gap-3">
            <Link to="/cart" onClick={() => setOpen(false)} className="flex-1 rounded-full bg-forest px-4 py-3 text-center text-xs font-bold uppercase tracking-[0.1em] text-white" data-testid="mobile-cart-link">Cart ({itemCount})</Link>
            <Link to={session.data?.user ? (session.data.user.role === "admin" ? "/admin" : "/account") : "/login"} onClick={() => setOpen(false)} className="flex-1 rounded-full border border-forest px-4 py-3 text-center text-xs font-bold uppercase tracking-[0.1em] text-forest" data-testid="mobile-account-link">Account</Link>
          </div>
          <a href={supportUrl} target="_blank" rel="noreferrer" className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-whatsapp px-4 py-3 text-xs font-bold uppercase tracking-[0.1em] text-white" data-testid="mobile-whatsapp-support-button"><MessageCircle size={14} /> WhatsApp support</a>
        </div>}
      </header>
    </>
  );
}

export function SiteFooter() {
  return <footer className="bg-forest text-cream" data-testid="site-footer">
    <div className="mx-auto grid max-w-[1380px] gap-12 px-5 py-16 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1.1fr] lg:px-10 lg:py-24">
      <div><Link to="/" className="inline-flex items-center gap-4 font-heading text-4xl font-semibold tracking-[-0.04em]" data-testid="footer-brand-link"><img src={LOGO_URL} alt="Micro Might logo" className="h-16 w-16 rounded-full border border-cream/20 object-cover" data-testid="footer-logo-image" /><span>Micro Might</span></Link><p className="mt-4 max-w-xs font-heading text-2xl leading-tight text-lime" data-testid="footer-tagline">From Our Trays To Your Plates</p><p className="mt-3 text-sm text-cream/65" data-testid="footer-secondary-tagline">Eat Green And Stay Lean</p></div>
      <div><p className="label text-lime" data-testid="footer-links-heading">Explore</p><div className="mt-5 grid gap-3">{navigation.slice(1, 6).map((item) => <Link key={item.to} to={item.to} className="text-sm text-cream/75 transition-colors duration-300 hover:text-white" data-testid={`footer-link-${item.label.toLowerCase().replaceAll(" ", "-").replaceAll(".", "")}`}>{item.label}</Link>)}</div></div>
      <div><p className="label text-lime" data-testid="footer-contact-heading">Find us</p><div className="mt-5 space-y-3 text-sm leading-relaxed text-cream/75"><p data-testid="footer-address">{ADDRESS}</p><a href={`tel:${PHONE_NUMBER}`} className="block hover:text-white" data-testid="footer-phone">Call {PHONE_NUMBER}</a><a href={`mailto:${EMAIL}`} className="block break-all hover:text-white" data-testid="footer-email">{EMAIL}</a><a href={whatsappUrl("Hi Micro Might, I'd like to know more about your microgreens.")} target="_blank" rel="noreferrer" className="block hover:text-white" data-testid="footer-whatsapp">WhatsApp {WHATSAPP_DISPLAY}</a></div></div>
      <div><p className="label text-lime" data-testid="footer-order-heading">Start fresh</p><p className="mt-5 text-sm leading-relaxed text-cream/75" data-testid="footer-order-copy">Build your cart, checkout as a guest, or sign in to keep your orders together.</p><Link to="/microgreens" className="mt-5 inline-flex items-center gap-2 rounded-full bg-lime px-5 py-3 text-xs font-bold uppercase tracking-[0.1em] text-forest transition-transform duration-300 hover:-translate-y-1" data-testid="footer-shop-button">Shop microgreens <ArrowRight size={15} /></Link></div>
    </div>
    <div className="border-t border-white/10"><div className="mx-auto flex max-w-[1380px] flex-col gap-3 px-5 py-5 text-[11px] text-cream/55 sm:flex-row sm:items-center sm:justify-between lg:px-10"><p data-testid="footer-license">FSSAI Lic. No. 21226010004732 · Gottigere, Bengaluru</p><p data-testid="footer-copyright">© 2026 Micro Might</p></div></div>
  </footer>;
}

export function SiteLayout({ children }: { children: ReactNode }) {
  return <div className="min-h-screen bg-cream text-ink"><SiteHeader /><main>{children}</main><SiteFooter /></div>;
}

export function PageIntro({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <section className="border-b border-line bg-cream px-5 pb-14 pt-16 sm:pb-20 sm:pt-24 lg:px-10 lg:pb-24 lg:pt-32" data-testid="page-intro"><div className="mx-auto max-w-[1380px]"><p className="label text-green" data-testid="page-intro-eyebrow">{eyebrow}</p><h1 className="mt-4 max-w-4xl font-heading text-5xl font-semibold leading-[0.96] tracking-[-0.05em] text-forest sm:text-6xl lg:text-8xl" data-testid="page-intro-title">{title}</h1><p className="mt-7 max-w-2xl text-base leading-relaxed text-ink/65 sm:text-lg" data-testid="page-intro-description">{description}</p></div></section>;
}

export function Reveal({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`animate-rise ${className}`}>{children}</div>;
}