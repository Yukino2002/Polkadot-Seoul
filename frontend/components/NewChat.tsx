'use client'

import { db } from '@/firebase';
import { PlusIcon } from '@heroicons/react/24/solid'
import { addDoc, collection, serverTimestamp } from 'firebase/firestore';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';


const NewChat = () => {
  const router = useRouter();
  const { data: session } = useSession();
  const createNewChat = async() => {
    const doc = await addDoc(
      collection(db, 'users', session?.user?.email!, 'chats'), {
        userId: session?.user?.email!,
        createdAt: serverTimestamp()
    }
    );

    router.push(`/chat/${doc.id}`)
  }
  return (
    <div onClick={createNewChat} className='border border-gray-400 chatRow'>
        <PlusIcon className='h-4 w-4'></PlusIcon>
        <p>New Chat</p>
    </div>
  )
}

export default NewChat