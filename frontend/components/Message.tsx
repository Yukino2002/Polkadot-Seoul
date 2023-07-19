import { DocumentData } from "firebase/firestore";

type Props = {
  message: DocumentData
}

const Message = ({
  message
}: Props) => {
  console.log(message)
  const isChatGPT = message.user.name === "ChatGPT";
  return (
    <div className={`py-5 text-white ${isChatGPT && "bg-gray-500/50"}`}>
      <div className="flex space-x-5 px-10 max-2-2xl mx-auto">
        <img src={message.user.avatar} alt="" className="h-8 w-8" />
        <p className="pt-1 text-sm">
          {message.text}
        </p>
      </div>
    </div>
  )
}

export default Message