'use client';

import { db } from "@/firebase";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";
import { addDoc, collection, doc, getDoc, serverTimestamp, setDoc } from "firebase/firestore";
import { useSession } from "next-auth/react";
import { FormEvent, useState } from "react";
import toast from "react-hot-toast";

type Props = {
  chatId: string;
}
const ChatInput = ({ chatId }: Props) => {
  const [prompt, setPrompt] = useState("");
  const { data: session } = useSession();

  const sendMessage = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!prompt) return;
    const input = prompt.trim();
    setPrompt("");

    const message: Message = {
      text: input,
      createdAt: serverTimestamp(),
      user: {
        _id: session?.user?.email!,
        name: session?.user?.name!,
        avatar: session?.user?.image! || `https://ui-avatars.com/api/?name=John+Doe`,
      }
    }

    await setDoc(doc(db, 'users', session?.user?.email!, 'chats', chatId, 'messages', Math.random().toString(36).substring(7)), {
      message
    });

    const notification = toast.loading("Sybil is thinking...")

    await fetch('/api/askQuestion', {
      method: 'POST',
      headers: {
        'Content-Type': 'applications/json',
        'Mnemonic': 'mnemonic',
        'Openai': 'fLXyttwdRNASlEr0SCAJT3BlbkFJCgiV1XTo2ivixng0vzRf',
      },
      body: JSON.stringify({
        prompt: input, chatId, session
      })
    }).then(() => {
      toast.success('Sybil responded', {
        id: notification,
      })
    })

  };
  return (
    <div className=" text-gray-300 rounded-lg text-sm flex justify-center py-5">
      <form onSubmit={sendMessage} className="bg-black rounded-lg p-3 space-x-5 flex w-full max-w-xl">
        <input type="text"
          className="bg-transparent px-3 focus:outline-none flex-1 disabled:cursor-not-allowed disabled:text-gray-300"
          disabled={!session}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Type command here"
        />
        <button type="submit" disabled={!prompt || !session} className="hover:opacity-75 text-white px-3 py-2 rounded disabled:cursor-not-allowed">
          <PaperAirplaneIcon className="h-5 w-5" />
        </button>
      </form>
      <div>
      </div>
    </div>
  )
}

export default ChatInput