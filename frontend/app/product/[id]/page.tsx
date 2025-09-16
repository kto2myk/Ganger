// maps: display_product.html -> /product/[id]
interface Props { params: { id: string } }
export default function ProductDetail({ params }: Props) {
  return <div><h1>Product #{params.id}</h1><p>Product detail placeholder.</p></div>;
}
