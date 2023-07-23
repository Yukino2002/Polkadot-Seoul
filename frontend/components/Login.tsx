'use client'
import { signIn } from "next-auth/react";
import Image from "next/image";

const clientId = "740744784364-bnsqukd5j3a920vvgnpn8ohg5h7ulgmk.apps.googleusercontent.com"

const Login = () => {
  return (
    <div className="bg-[#111111] h-screen flex flex-col items-center justify-center text-center ">
      <div>
        
      </div>
      <Image 
      src = "https://imgur.com/usI3OTw.png"
      width={100}
      height={100}
      alt="Logo"
      className="rotate"
      />
      <Image 
      src = "https://i.imgur.com/TQK3iD2.png"
      width={300}
      height={300}
      alt="Logo"
      />
      <br></br>
      <button onClick={() => signIn('google')} className="border border-blue-400 rounded-lg px-5 py-2 hover:bg-gray-900 text-white text-2xl ">Google Sign in</button>
    </div>
  )
}

export default Login