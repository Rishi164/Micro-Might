import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, ShoppingBag } from "lucide-react";
import { toast } from "sonner";
import { Link } from "react-router-dom";
import { PageIntro, SiteLayout } from "@/components/SiteShell";
import ProductCard from "@/components/ProductCard";
import { products, signatureMix } from "@/lib/products";
import { useCart } from "@/components/CartProvider";
import { apiGet } from "@/lib/api";
import type { InventoryItem } from "@/lib/types";

export default function Microgreens() {
  const [mixWeight, setMixWeight] = useState<"50g" | "100g">("50g");
  const { addItem } = useCart();
  const inventoryQuery = useQuery({ queryKey: ["inventory"], queryFn: () => apiGet<InventoryItem[]>("/inventory"), retry: false });
  const mixInventory = inventoryQuery.data?.find((item) => item.product_slug === "signature-mix");
  const mixAvailable = mixWeight === "50g" ? mixInventory?.stock_50g : mixInventory?.stock_100g;
  const mixOutOfStock = mixInventory?.tracking_enabled === true && mixAvailable === 0;
  return (
    <SiteLayout>
      <PageIntro
        eyebrow="Our microgreens"
        title="Freshly grown varieties, from our trays to your plates."
        description="Explore our current collection of 14 individual microgreens, each grown with care in Gottigere, Bengaluru. Choose regular freshness or ask us to grow a variety specially for you through G.Y.O.C."
      />
      <section className="bg-cream px-5 py-14 sm:py-20 lg:px-10 lg:py-28" data-testid="catalog-section">
        <div className="mx-auto max-w-[1380px]">
          <div className="mb-10 flex flex-col gap-3 border-b border-line pb-6 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="label text-green" data-testid="catalog-label">14 varieties · two ways to order</p>
              <h2 className="mt-2 font-heading text-4xl font-semibold text-forest sm:text-5xl" data-testid="catalog-title">Choose your green.</h2>
            </div>
            <Link to="/gyoc" className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[0.12em] text-forest" data-testid="catalog-gyoc-link">What is G.Y.O.C.? <ArrowRight size={15} /></Link>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {products.map((product) => <ProductCard key={product.slug} product={product} />)}
          </div>

          <div className="mt-16 overflow-hidden rounded-[2rem] border border-forest/10 bg-forest text-cream" data-testid="signature-mix-card">
            <div className="grid lg:grid-cols-[0.8fr_1.2fr]">
              <img src={signatureMix.image} alt="Micro Might Signature Mix salad with fresh microgreens" loading="lazy" className="h-72 w-full object-cover lg:h-full" data-testid="signature-mix-image" />
              <div className="p-7 sm:p-10 lg:p-14">
                <p className="label text-lime" data-testid="signature-mix-eyebrow">Only as a regular mix</p>
                <h2 className="mt-3 font-heading text-5xl font-semibold leading-none tracking-[-0.05em]" data-testid="signature-mix-name">{signatureMix.name}</h2>
                <p className="mt-4 max-w-lg text-base leading-relaxed text-cream/70" data-testid="signature-mix-description">{signatureMix.description} A changing balance of fresh textures and colours, prepared as our house mix.</p>
                <div className="mt-8 flex flex-wrap gap-3">
                  <button type="button" onClick={() => setMixWeight("50g")} className={`rounded-xl border px-5 py-4 text-left ${mixWeight === "50g" ? "border-lime bg-lime/10" : "border-white/15"}`} data-testid="signature-mix-50g-option"><p className="text-[10px] font-bold uppercase tracking-[0.15em] text-lime">50g</p><p className="mt-1 font-heading text-3xl">₹{signatureMix.regular.small}</p></button>
                  <button type="button" onClick={() => setMixWeight("100g")} className={`rounded-xl border px-5 py-4 text-left ${mixWeight === "100g" ? "border-lime bg-lime/10" : "border-white/15"}`} data-testid="signature-mix-100g-option"><p className="text-[10px] font-bold uppercase tracking-[0.15em] text-lime">100g</p><p className="mt-1 font-heading text-3xl">₹{signatureMix.regular.large}</p></button>
                </div>
                <p className="mt-6 max-w-md text-sm leading-relaxed text-cream/60" data-testid="signature-mix-gyoc-note">G.Y.O.C. is available for customers choosing an individual variety. Signature Mix is available only as our regular mixed product.</p>
                <p className={`mt-6 text-xs font-semibold ${mixOutOfStock ? "text-red-200" : "text-lime"}`} data-testid="signature-mix-stock">{mixInventory?.tracking_enabled ? `${mixAvailable} ${mixWeight} packs available` : "Available — stock count pending admin setup"}</p>
                <button type="button" disabled={mixOutOfStock} onClick={() => { addItem({ productSlug: "signature-mix", name: signatureMix.name, variety: signatureMix.variety, plan: "regular", weight: mixWeight, unitPrice: mixWeight === "50g" ? signatureMix.regular.small : signatureMix.regular.large, image: signatureMix.image }); toast.success("Signature Mix added to cart"); }} className="mt-3 inline-flex items-center gap-2 rounded-full bg-lime px-6 py-4 text-xs font-bold uppercase tracking-[0.1em] text-forest disabled:cursor-not-allowed disabled:bg-cream/20 disabled:text-cream/50" data-testid="signature-mix-add-button"><ShoppingBag size={15} /> {mixOutOfStock ? "Out of stock" : "Add Signature Mix to cart"}</button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}