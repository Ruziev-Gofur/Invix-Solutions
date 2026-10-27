import type { Product } from "./types";
export const demoProducts: Product[] = ["Headphones", "Backpack", "Watch", "Sneakers"].map((title, i) => ({ id: i + 1, title, image_url: "/demo-product.svg", created_at: "2026-01-01T00:00:00Z" }));
