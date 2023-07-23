'use client'

import ChatParent from '@/components/ChatParent'

type Props = {
  params: {
    id: string
  }
}

const ChatPage = ({ params: { id } }: Props) => {
  return (
    <ChatParent id={id} />
  )
}

export default ChatPage