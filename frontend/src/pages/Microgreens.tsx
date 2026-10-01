import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { PageIntro, SiteLayout } from "@/components/SiteShell";
import ProductCard from "@/components/ProductCard";
import { productOrderUrl } from "@/lib/brand";
import { products, signatureMix } from "@/lib/products";

export default function Microgreens() {
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
                  <div className="rounded-xl border border-white/15 px-5 py-4"><p className="text-[10px] font-bold uppercase tracking-[0.15em] text-lime">50g</p><p className="mt-1 font-heading text-3xl">₹{signatureMix.regular.small}</p></div>
                  <div className="rounded-xl border border-white/15 px-5 py-4"><p className="text-[10px] font-bold uppercase tracking-[0.15em] text-lime">100g</p><p className="mt-1 font-heading text-3xl">₹{signatureMix.regular.large}</p></div>
                </div>
                <p className="mt-6 max-w-md text-sm leading-relaxed text-cream/60" data-testid="signature-mix-gyoc-note">G.Y.O.C. is available for customers choosing an individual variety. Signature Mix is available only as our regular mixed product.</p>
                <a href={productOrderUrl(signatureMix.name, signatureMix.variety, "50g")} target="_blank" rel="noreferrer" className="mt-8 inline-flex items-center gap-2 rounded-full bg-whatsapp px-6 py-4 text-xs font-bold uppercase tracking-[0.1em] text-white" data-testid="signature-mix-order-button">Order Signature Mix <ArrowRight size={15} /></a>
              </div>
            </div>
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}