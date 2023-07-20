'use client'

import { db } from "@/firebase";
import { collection, query, getDocs } from "firebase/firestore";
import { useSession } from "next-auth/react";
import { useCollection } from "react-firebase-hooks/firestore";
import Message from "./Message";
import { ArrowUpCircleIcon } from "@heroicons/react/24/solid";
import { useEffect, useState } from "react";

type Props = {
  chatId: string,
  setReload: any,
  reload: any
}

const Chat = ({ chatId, reload, setReload }: Props) => {
  const { data: session } = useSession();
  const [messagesData, setMessagesData] = useState<any[]>([])
  // let messagesData: any = []
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
