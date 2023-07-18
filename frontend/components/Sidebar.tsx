'use client'

import { db } from '@/firebase'
import NewChat from './NewChat'
import { useSession, signOut } from 'next-auth/react'
import { useCollection } from "react-firebase-hooks/firestore"
import { collection, orderBy, query } from 'firebase/firestore'
import ChatRow from './ChatRow'

const Sidebar = () => {
  const { data: session } = useSession();
  const [chats, loading, error] = useCollection(
    session && query(
      collection(db, 'users', session.user?.email!, 'chats'), orderBy('createdAt', 'asc'))
  );
  return (
    <div className='p-2 flex flex-col h-screen'>
        <div className='flex-1'>
            <div>
                {/* New Chat button */}
                <NewChat />
                <div className='flex flex-col space-y-2 my-2'>
                  {loading && (
                    <div className='animate-pulse text-center text-white'>
                      <p>Loading chats...</p>
                    </div>
                  )}
                  {/* Map through the ChatRows */}
                  {chats?.docs.map(chat => (
                    <ChatRow key={chat.id} id={chat.id} />
                  ))}
                </div>
            </div>
        </div>
        <div className="flex justify-center items-center py-2 border-t border-gray-500">
          <button
            onClick={() => signOut()}
            className="flex text-white flex-row justify-center items-center space-x-4 py-2 px-10 rounded hover:bg-[#1e1e1e]"
          >
            {session && (
              <img
                src={session.user?.image!}
                alt="Profile Pic"
                className="h-10 w-10 rounded-full cursor-pointer mx-auto mb-2"
              />
            )}
            <span className="mx-auto">Logout</span>
          </button>
        </div>

    </div>
  )
}

export default Sidebar