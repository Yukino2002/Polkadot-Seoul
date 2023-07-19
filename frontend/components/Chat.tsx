'use client'

import { db } from "@/firebase";
import { collection, query, getDocs } from "firebase/firestore";
import { useSession } from "next-auth/react";
import { useCollection } from "react-firebase-hooks/firestore";
import Message from "./Message";
import { ArrowUpCircleIcon } from "@heroicons/react/24/solid";
import { useState } from "react";

type Props = {
  chatId: string;
}

const Chat = ({ chatId }: Props) => {
  const { data: session } = useSession();
  const [messagesData, setMessagesData] = useState<any[]>([])
  const messagesPath = `users/${session?.user?.email}/chats/${chatId}/messages`;

  // Fetch the documents and instantiate the messages array
  const fetchMessages = async () => {
    try {
      const messagesCollection = collection(db, messagesPath);
      const querySnapshot = await getDocs(messagesCollection);
      const messages = querySnapshot.docs.map((doc) => doc.data());

      return messages;
    } catch (error) {
      console.error("Error fetching messages:", error);
      return [];
    }
  };

  fetchMessages().then((messages) => setMessagesData(messages));

  return (
    <div className="flex-1 overflow-y-auto overflow-x-hidden">
      {messagesData.length === 0 && (
        <>
          <ArrowUpCircleIcon className="h-10 w-10 mx-auto mt-5 text-white animate-bounce" />
          <p className="mt-3 text-center text-white">
            Type a prompt to get started
          </p>
        </>
      )}
      {messagesData.map((message: any) => (
        <Message key={message.id} message={message.message} />
      ))}
    </div>
  )
}

export default Chat
