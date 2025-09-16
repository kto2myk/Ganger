// maps: shop_categorized_page.html -> /shop/category/[category]
interface Props { params: { category: string } }
export default function ShopCategoryPage({ params }: Props) {
  return <div><h1>Category: {params.category}</h1><p>Category list placeholder.</p></div>;
}
