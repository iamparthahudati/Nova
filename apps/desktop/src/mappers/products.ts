import type { ProductResponse, ProductsResponse } from '@nova/api-contracts'
import type { Product } from '@/view-models'

export function mapProduct(row: ProductResponse): Product {
  return {
    id: row.id,
    name: row.name,
    store: row.store ?? undefined,
    status: row.status,
    price: row.price ?? undefined,
    soldCount: row.sold_count,
    createdAt: row.created_at,
  }
}

export function mapProducts(response: ProductsResponse): Product[] {
  return response.products.map(mapProduct)
}
