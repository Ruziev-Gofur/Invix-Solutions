import Link from "next/link";
import { productsCount } from "@/lib/plural";
import type { Product } from "@/lib/types";

// Каталог всегда свежий: данные берутся при каждом запросе
export const dynamic = "force-dynamic";

const API = process.env.API_INTERNAL_URL ?? "http://backend:8000";

async function getProducts(offset: number): Promise<Product[] | null> {
  if (process.env.DEMO_MODE === "true") {
    const { demoProducts } = await import("@/lib/demo-products");
    return demoProducts.slice(offset, offset + 25);
  }
  try {
    const res = await fetch(`${API}/api/products?limit=25&offset=${offset}`, { cache: "no-store", signal: AbortSignal.timeout(10000) });
    if (!res.ok) return null;
    return (await res.json()) as Product[];
  } catch {
    return null;
  }
}

export default async function CatalogPage({ searchParams }: { searchParams: Promise<{ page?: string }> }) {
  const { page: rawPage } = await searchParams;
  const parsed = Number(rawPage ?? 1);
  const page = Number.isSafeInteger(parsed) && parsed > 0 && parsed <= 1000000 ? parsed : 1;
  const products = await getProducts((page - 1) * 24);

  return (
    <main className="page">
      {process.env.DEMO_MODE === "true" && <p className="note">Demo catalog</p>}
      <header className="head">
        <h1>Catalog</h1>
        {products && products.length > 0 && <p className="count">{productsCount(Math.min(products.length, 24))}</p>}
      </header>

      {products === null ? (
        <p className="note">Не удалось загрузить каталог. Обновите страницу через минуту.</p>
      ) : products.length === 0 ? (
        <p className="note">Пока нет товаров. Первый добавит администратор через бота.</p>
      ) : (
        <ul className="grid">
          {products.slice(0, 24).map((p) => (
            <li key={p.id} className="item">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={p.image_url} alt={p.title} loading="lazy" className="photo" />
              <span className="title">{p.title}</span>
            </li>
          ))}
        </ul>
      )}
      <nav aria-label="Catalog pages" className="pagination">
        {page > 1 && <Link href={"?page=" + (page - 1)}>Previous</Link>}
        <span>Page {page}</span>
        {products && products.length > 24 && <Link href={"?page=" + (page + 1)}>Next</Link>}
      </nav>
    </main>
  );
}
