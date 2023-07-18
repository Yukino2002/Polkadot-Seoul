import Chat from '@/components/Chat'
import ChatInput from '@/components/ChatInput'

type Props = {
  params: {
    id:string
  }
}

const ChatPage = ({params:{ id }}: Props) => {
  return (
    <div className='flex flex-col h-screen overflow-hidden'>
      <ChatInput chatId={id} />
      <Chat chatId={id}/>
    </div>
  )
}

export default ChatPage