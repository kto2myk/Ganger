// maps: image_display.html -> /image/[id]
interface Props { params: { id: string } }
export default function ImageDisplayPage({ params }: Props) {
  return <div><h1>Image {params.id}</h1><p>Image display placeholder.</p></div>;
}
