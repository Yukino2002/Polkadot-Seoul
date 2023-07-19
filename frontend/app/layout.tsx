import Sidebar from '@/components/Sidebar'
import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { SessionProvider } from '@/components/SessionProvider'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/pages/api/auth/[...nextauth]'
import Login from '@/components/Login'
import ClientProvider from '@/components/ClientProvider'
import RightSidebar from '@/components/RightSidebar'

import { db } from "@/firebase"
import { collection, query, doc, where, setDoc, getDocs } from 'firebase/firestore'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Sybil AI',
  description: 'EZ chatbot',
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await getServerSession(authOptions)

  if (session) {
    // Check if user exists in users collection
    const usersQuery = query(
      collection(db, 'users'),
      where('_id', '==', session?.user?.email!)
    );

    const usersSnapshot = await getDocs(usersQuery);

    if (usersSnapshot.empty) {
      // User does not exist in the collection, add user to users collection
      await setDoc(doc(db, 'users', session?.user?.email!), {
        _id: session?.user?.email!,
        name: session?.user?.name!,
        avatar: session?.user?.image! || `https://ui-avatars.com/api/?name=John+Doe`,
      });

      // create empty chats collection for user
      await setDoc(doc(db, 'users', session?.user?.email!, 'chats', 'default'), {
        _id: 'default',
        name: 'default',
        messages: []
      });
    }
  }

  return (
    <html lang="en">
      <body className={inter.className}>
        <SessionProvider session={session}>
          {!session ? (
            <Login />
          ) : (
            <div className='flex'>
              {/* Left Sidebar */}
              <div className='bg-[#111111] max-w-xs h-screen overflow-y-auto md:min-w-[20rem]'>
                <Sidebar />
              </div>

              {/* Content */}
              <div className='bg-[#1C1C1C] flex-grow'>
                {/* ClientProvider - Notification */}
                <ClientProvider />
                {children}
              </div>

              {/* Right Sidebar */}
              <div className='bg-[#111111] max-w-xs h-screen overflow-y-auto md:min-w-[20rem]'>
                <RightSidebar />
              </div>
            </div>
          )}
        </SessionProvider>
      </body>
    </html>
  )
}
