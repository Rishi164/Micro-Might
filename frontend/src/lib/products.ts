import type { EnjoymentIdea, MicrogreenProduct } from "@/lib/types";

const images = {
  hero: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/b2df64d7a30f9d1b60fcfc19a274a9695d2afccc5d3ea5e7379a5ba9900cc160.jpeg",
  wheatgrass: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/77e64258e94310df6945adffd9c873d9e51a6e5f1ddd6ce81326209dc82e0e6b.jpeg",
  sunflower: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/819b77f6a892f23498935de9aeae154922040709927d89a9f807af14aeb502dd.jpeg",
  pea: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/b3ad407391534734f2af2d35669a2819deac0cc6d641f475b1efdadc493fddd2.jpeg",
  redRadish: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/0cc4eb4036310f8c466a0b580bca708431cbeb58f46e4f19686f3811d6ca3008.jpeg",
  mustard: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/2d552c660e8ec689fbc708c80ddf423a910741b1d348d00c801046e258ecdc7c.jpeg",
  methi: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/12dc10fabcf2938093d26d333301a32dede15da97cc21936898d393a291081bb.jpeg",
  spinach: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/c05aa95fec8ad9c474c6d8c9aff9194dc810af2bfa9665272e37e4b099b0f01c.jpeg",
  beetroot: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/447dcb4d6f9c7581128ff816856ad4be1321e82fcb0bb639d714533e2f24b454.jpeg",
  broccoli: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/a1529559717196efde4e364a95c8417c3748d251cc6718128335b93f334f9754.jpeg",
  basil: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/e6943aadd9ca330fbe1108a6fee263d14d137773512abcfd097bec1841ee59fe.jpeg",
  chia: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/0f703418566392e972d036b4e886934f4da816db191ace8dc37eaae8d8a8049f.jpeg",
  celery: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/0669fd5cb942df4283dd98f2ad4eb4ac690c48159c2ee3ad7fbd0820c15fa067.jpeg",
  corn: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/289ee9fe5484d67d0bbced3465b44c513449ba05cb12243eec0d7a18be92742a.jpeg",
  redAmaranthus: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/82abb3e6e2764de8299433b726c26bb81fece3b0aa2129b0bc2744b65bff4413.jpeg",
  salad: "https://static.prod-images.emergentagent.com/jobs/d4509cc0-f2be-441a-8a8f-d50475c28144/images/715f0d6ff84201f7318284374dadc99776e49b74a40b96a8be88ea6b365209f1.jpeg",
};

const productRows: [string, string, string, string, [number, number], [number, number], string][] = [
  ["emerald-vital", "Emerald Vital", "Wheatgrass", "Tall, clean and vibrant with a fresh grassy character.", [79, 149], [99, 169], images.wheatgrass],
  ["golden-crunch", "Golden Crunch", "Sunflower", "Broad leaves, a satisfying bite and a gentle nuttiness.", [89, 159], [109, 179], images.sunflower],
  ["verdant-rise", "Verdant Rise", "Pea", "Tender tendrils with a naturally sweet, garden-fresh finish.", [99, 179], [119, 199], images.pea],
  ["ruby-blaze", "Ruby Blaze", "Red Radish", "Colourful stems with a lively peppery lift.", [94, 176], [114, 196], images.redRadish],
  ["golden-spice", "Golden Spice", "Mustard", "Fine leaves with a warm, gently spicy edge.", [79, 149], [99, 169], images.mustard],
  ["herbal-gold", "Herbal Gold", "Methi / Fenugreek", "Delicate greens with a distinctive herbal note.", [79, 149], [99, 169], images.methi],
  ["emerald-leaf", "Emerald Leaf", "Spinach", "Small, tender leaves made for everyday meals.", [89, 169], [109, 189], images.spinach],
  ["crimson-root", "Crimson Root", "Beetroot", "Jewel-toned stems that bring colour to every plate.", [119, 219], [139, 239], images.beetroot],
  ["emerald-crown", "Emerald Crown", "Broccoli", "Fresh, compact and quietly versatile.", [119, 219], [139, 239], images.broccoli],
  ["royal-basil", "Royal Basil", "Basil", "Aromatic young leaves with a bright basil finish.", [119, 219], [139, 239], images.basil],
  ["vital-seed", "Vital Seed", "Chia", "Fine, delicate greens with a clean, soft texture.", [99, 179], [119, 199], images.chia],
  ["green-crisp", "Green Crisp", "Celery", "Fragrant, feathery greens with a fresh celery lift.", [119, 219], [139, 239], images.celery],
  ["golden-silk", "Golden Silk", "Corn", "Sunny, slender blades with a subtle sweetness.", [89, 169], [109, 189], images.corn],
  ["crimson-jewel", "Crimson Jewel", "Red Amaranthus", "Vivid crimson colour with a delicate fresh crunch.", [109, 199], [129, 219], images.redAmaranthus],
];

export const products: MicrogreenProduct[] = productRows.map(([slug, name, variety, description, regular, gyoc, image]) => ({
  slug,
  name,
  variety,
  description,
  regular: { small: regular[0], large: regular[1] },
  gyoc: { small: gyoc[0], large: gyoc[1] },
  image,
}));

export const signatureMix = {
  name: "Micro Might Signature Mix",
  variety: "Mixed Microgreens",
  description: "A colourful everyday mix for adding freshness and texture to meals.",
  image: images.salad,
  regular: { small: 109, large: 204 },
};

export const enjoymentIdeas: EnjoymentIdea[] = [
  { title: "Salads", description: "Add colour, texture and a fresh finish.", image: images.salad },
  { title: "Sandwiches", description: "Layer a generous handful between slices.", image: images.sunflower },
  { title: "Wraps & Rolls", description: "Bring a crisp green note to every bite.", image: images.redRadish },
  { title: "Breakfast", description: "Finish eggs, toast or savoury bowls.", image: images.wheatgrass },
  { title: "Bowls & Meals", description: "Top everyday meals just before serving.", image: images.broccoli },
  { title: "Smoothies", description: "Blend a small handful into your routine.", image: images.pea },
];

export { images };