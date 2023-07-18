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
  return (
    <html lang="en">
      <body className={inter.className}>
        <SessionProvider session={session}>
          {!session ? (
            <Login />
          ):(
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
