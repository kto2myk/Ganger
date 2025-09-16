// maps: message_room.html -> /messages/[roomId]
interface Props { params: { roomId: string } }
export default function MessageRoomPage({ params }: Props) {
  return <div><h1>Room {params.roomId}</h1><p>Messages placeholder.</p></div>;
}
