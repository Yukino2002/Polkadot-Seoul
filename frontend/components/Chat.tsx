import { useEffect, useState } from "react";
import { db } from "@/firebase";
import { collection, getDocs } from "firebase/firestore";
import { useSession } from "next-auth/react";
import Message from "./Message";

type Props = {
  chatId: string,
  setReload: any,
  reload: any
}

const Chat = ({ chatId, reload, setReload }: Props) => {
  const { data: session } = useSession();
  const [messagesData, setMessagesData] = useState<any[]>([]);
  const messagesPath = `users/${session?.user?.email}/chats/${chatId}/messages`;

  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const messagesCollection = collection(db, messagesPath);
        const querySnapshot = await getDocs(messagesCollection);
        let messages = querySnapshot.docs.map((doc) => doc.data());

        messages.sort((a, b) => {
          return a.message.createdAt.seconds - b.message.createdAt.seconds
        })

        setMessagesData(messages);
      } catch (error) {
        console.error("Error fetching messages:", error);
      }
    };

    fetchMessages();
  }, [messagesPath, reload])

  return (
    <div className="flex-1 overflow-y-auto overflow-x-hidden">
      {messagesData.length === 0 && (
        <p className="mt-3 text-center text-white">
          Type a prompt to get started
        </p>
      )}
      {messagesData.map((message: any, index: number) => (
        <Message key={message.id} message={message.message} isBotMessage={index % 2 !== 0} />
      ))}
    </div>
  )
}

export default Chat
