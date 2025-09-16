// maps: display_post.html -> /post/[id]
interface Props { params: { id: string } }
export default function PostDetailPage({ params }: Props) {
  return <div><h1>Post #{params.id}</h1><p>Post detail placeholder.</p></div>;
}
