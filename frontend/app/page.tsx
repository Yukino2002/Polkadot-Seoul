import React from 'react'
import Image from 'next/image'
import './globals.css'

function page() {
  return (
    <div className='flex flex-col items-center justify-center h-screen px-2 text-white'>
      <Image
        src = "https://i.imgur.com/sGqjkxG.png"
        width={200}
        height={200}
        alt="Logo"
      />
    </div>
  )
}

export default page