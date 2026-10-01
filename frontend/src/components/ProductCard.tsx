import { useRef, useState } from "react";
import { ShoppingBag } from "lucide-react";
import { toast } from "sonner";
import type { MicrogreenProduct } from "@/lib/types";
import { useCart } from "@/components/CartProvider";

export default function ProductCard({ product }: { product: MicrogreenProduct }) {
  const [plan, setPlan] = useState<"regular" | "gyoc">("regular");
  const [weight, setWeight] = useState<"50g" | "100g">("50g");
  const planRef = useRef<"regular" | "gyoc">("regular");
  const weightRef = useRef<"50g" | "100g">("50g");
  const prices = plan === "regular" ? product.regular : product.gyoc;
  const { addItem } = useCart();

  function choosePlan(value: "regular" | "gyoc") {
    planRef.current = value;
    setPlan(value);
  }

  function chooseWeight(value: "50g" | "100g") {
    weightRef.current = value;
    setWeight(value);
  }

  return <article className="group flex h-full flex-col overflow-hidden rounded-2xl border border-line bg-white shadow-[0_8px_30px_rgba(0,0,0,0.04)] transition-transform duration-300 hover:-translate-y-1 hover:shadow-[0_20px_50px_rgba(20,54,33,0.1)]" data-testid={`product-card-${product.slug}`}>
    <div className="relative aspect-[1.1] overflow-hidden bg-sage"><img src={product.image} alt={`${product.variety} microgreens for ${product.name}`} loading="lazy" className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" data-testid={`product-image-${product.slug}`} /><span className="absolute left-4 top-4 rounded-full bg-cream/90 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-forest" data-testid={`product-variety-${product.slug}`}>{product.variety}</span></div>
    <div className="flex flex-1 flex-col p-5 sm:p-6"><div><h3 className="font-heading text-3xl font-semibold leading-none tracking-[-0.04em] text-forest" data-testid={`product-name-${product.slug}`}>{product.name}</h3><p className="mt-3 text-sm leading-relaxed text-ink/60" data-testid={`product-description-${product.slug}`}>{product.description}</p></div>
      <div className="mt-6 rounded-xl bg-cream p-3" data-testid={`product-pricing-${product.slug}`}><div className="flex rounded-lg bg-white p-1"><button type="button" onClick={() => choosePlan("regular")} className={`flex-1 rounded-md px-2 py-2 text-[10px] font-bold uppercase tracking-[0.12em] ${plan === "regular" ? "bg-forest text-cream" : "text-ink/50"}`} aria-pressed={plan === "regular"} data-testid={`product-regular-tab-${product.slug}`}>Regular</button><button type="button" onClick={() => choosePlan("gyoc")} className={`flex-1 rounded-md px-2 py-2 text-[10px] font-bold uppercase tracking-[0.12em] ${plan === "gyoc" ? "bg-lime text-forest" : "text-ink/50"}`} aria-pressed={plan === "gyoc"} data-testid={`product-gyoc-tab-${product.slug}`}>G.Y.O.C.</button></div><div className="mt-4 flex items-end justify-between gap-3"><div><p className="text-[10px] font-bold uppercase tracking-[0.14em] text-green" data-testid={`product-plan-label-${product.slug}`}>{plan === "regular" ? "Fresh regular" : "Grown specially for you"}</p><div className="mt-2 flex gap-2"><button type="button" onClick={() => chooseWeight("50g")} className={`rounded-full border px-3 py-1.5 text-xs font-bold ${weight === "50g" ? "border-forest bg-forest text-white" : "border-line text-ink/55"}`} data-testid={`product-50g-option-${product.slug}`}>50g ₹{prices.small}</button><button type="button" onClick={() => chooseWeight("100g")} className={`rounded-full border px-3 py-1.5 text-xs font-bold ${weight === "100g" ? "border-forest bg-forest text-white" : "border-line text-ink/55"}`} data-testid={`product-100g-option-${product.slug}`}>100g ₹{prices.large}</button></div></div><span className="font-heading text-4xl font-semibold leading-none text-forest" data-testid={`product-selected-price-${product.slug}`}>₹{weight === "50g" ? prices.small : prices.large}</span></div></div>
      <button type="button" onClick={() => { const selectedPlan = planRef.current; const selectedWeight = weightRef.current; const selectedPrices = selectedPlan === "regular" ? product.regular : product.gyoc; addItem({ productSlug: product.slug, name: product.name, variety: product.variety, plan: selectedPlan, weight: selectedWeight, unitPrice: selectedWeight === "50g" ? selectedPrices.small : selectedPrices.large, image: product.image }); toast.success(`${product.name} added to cart`); }} className="mt-5 inline-flex items-center justify-center gap-2 rounded-full bg-forest px-4 py-3 text-xs font-bold uppercase tracking-[0.1em] text-white transition-transform duration-300 hover:-translate-y-1" data-testid={`product-add-button-${product.slug}`}><ShoppingBag size={15} /> Add to cart</button>
    </div>
  </article>;
}