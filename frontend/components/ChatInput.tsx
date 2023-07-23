'use client';

import { db } from "@/firebase";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";
import { addDoc, collection, doc, getDoc, serverTimestamp, setDoc } from "firebase/firestore";
import { useSession } from "next-auth/react";
import { FormEvent, useState, useEffect } from "react";
import toast from "react-hot-toast";
import io from 'socket.io-client';

type Props = {
  chatId: string,
  setReload: any,
  reload: any
}
const ChatInput = ({ chatId, setReload, reload }: Props) => {
  const [prompt, setPrompt] = useState("");
  const { data: session } = useSession();
  const [socket, setSocket] = useState(null);

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

    setReload((prevReload: any) => !prevReload)

    const notification = toast.loading("Sybil is thinking...")
    let openAIKey = localStorage.getItem('openAIKey') || '';
    console.log('openAIKey after getting from localStorage:', openAIKey); // new debug line

    openAIKey = openAIKey.startsWith('sk-') ? openAIKey.substring(3) : openAIKey;

    await fetch('/api/askQuestion', {
      method: 'POST',
      headers: {
        'Content-Type': 'applications/json',
        'Mnemonic': 'mnemonic',
        'Openai': openAIKey, // use the key from local storage
      },
      body: JSON.stringify({
        prompt: input, chatId, session
      })
    }).then(() => {
      toast.success('Sybil responded', {
        id: notification,
      })
      setReload((prevReload: any) => !prevReload)
    })
  };

    useEffect(() => {
      const socketIOClient = io('http://localhost:5000');
      if(socket) {
        socket.emit('query', {'test': 'test'});
      }

      socketIOClient.on('response', (data) => {
          console.log(data);
          handleData(data);
      });

      setSocket(socketIOClient);

      return () => {
          socketIOClient.disconnect();
      };
  }, []);

    const handleData = async (data) => {

        if ('chatId' in data) {
          // Do something with chatId
          console.log('Chat ID:', data.chatId);
          console.log('Session:', data.session);
          console.log('Prompt:', data.prompt);
          const createdAt = new Date(data.createdAt);

          const message: Message = {
            text: data.prompt,
            createdAt: createdAt,
            user: {
              _id: data.session?.user?.email!,
              name: data.session?.user?.name!,
              avatar: data.session?.user?.image! || `https://ui-avatars.com/api/?name=John+Doe`,
            }
          }

          await setDoc(doc(db, 'users', data.session?.user?.email!, 'chats', data.chatId, 'messages', Math.random().toString(36).substring(7)), {
            message
          });
          setReload((prevReload: any) => !prevReload)

      } else {
          console.error('Data received without chatId:', data);
      }
    };

    const sendQuery = async (e: FormEvent<HTMLFormElement>) =>{
      e.preventDefault()
      if(socket) {
        if (!prompt) return;
        const input = prompt.trim();
        setPrompt("");
        const message: Message = {
          text: input,
          createdAt: await serverTimestamp(),
          user: {
            _id: session?.user?.email!,
            name: session?.user?.name!,
            avatar: session?.user?.image! || `https://ui-avatars.com/api/?name=John+Doe`,
          }
        }
        let openAIKey = localStorage.getItem('openAIKey');
        let mnenonic = localStorage.getItem('mnemonicKey');
        let res = JSON.stringify({
          prompt: input, chatId, session, "openAIKey": openAIKey, "mnenonic": mnenonic
        })
        socket.emit('print', res);
        await setDoc(doc(db, 'users', session?.user?.email!, 'chats', chatId, 'messages', Math.random().toString(36).substring(7)), {
          message
        }); 

      }
  };

  return (
    <div className=" text-gray-300 rounded-lg text-sm flex justify-center py-5">
      <form onSubmit={sendQuery} className="bg-black rounded-lg p-3 space-x-5 flex w-full max-w-xl">
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