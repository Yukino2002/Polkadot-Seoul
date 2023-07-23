'use Client'

import ChatInput from "./ChatInput"
import Chat from "./Chat"

import { useState } from "react"

const ChatParent = ({ id }: any) => {
  const [reload, setReload] = useState(false)
  return (
    <div className='flex flex-col h-screen overflow-hidden'>
      <ChatInput chatId={id} setReload={setReload} reload={reload} />
      <Chat chatId={id} setReload={setReload} reload={reload} />
    </div>
  )
}

export default ChatParent