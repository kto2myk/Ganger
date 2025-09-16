// maps: my_profile.html -> /profile/[username]
interface Props { params: { username: string } }
export default function ProfilePage({ params }: Props) {
  return <div><h1>Profile: {params.username}</h1><p>Public profile placeholder.</p></div>;
}
