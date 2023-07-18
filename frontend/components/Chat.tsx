'use client'

import { db } from "@/firebase";
import { collection, orderBy, query } from "firebase/firestore";
import { useSession } from "next-auth/react";
import { useCollection } from "react-firebase-hooks/firestore";
import Message from "./Message";
import {  ArrowUpCircleIcon } from "@heroicons/react/24/solid";

type Props = {
    chatId: string;
}

const Chat = ({ chatId }: Props) => {
    const { data: session } = useSession();

    const [ messages ] = useCollection(
      session && 
      query(
        collection(
          db, 
          "users", 
          session?.user?.email!, 
          "chats", 
          chatId, 
          "messages"
          ),
          orderBy("createdAt", "asc")
      )
    );
  return (
    <div className="flex-1 overflow-y-auto overflow-x-hidden">
        {messages?.empty && (
          <>
            <ArrowUpCircleIcon className="h-10 w-10 mx-auto mt-5 text-white animate-bounce" />
            <p className="mt-3 text-center text-white">
              Type a prompt to get started
            </p>
          </>
        )}
        {messages?.docs.map((message) => (
            <Message key={message.id} message ={message.data()}/>
        ))}
    </div>
  )
}

export default Chat