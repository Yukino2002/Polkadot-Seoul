import { DocumentData } from "firebase/firestore";

type Props = {
  message: DocumentData,
  isBotMessage: boolean
}

const Message = ({
  message,
  isBotMessage
}: Props) => {
  console.log(message)

  const handleYesNoClick = (choice: string) => {
    console.log(`User selected: ${choice}`);
  }

  return (
    <div className="py-5 text-white">
      <div className="flex space-x-5 px-10 max-2-2xl mx-auto">
        <img src={message.user.avatar} alt="" className="h-8 w-8" />
        <p className="pt-1 text-sm">
          {message.text}
        </p>
      </div>
      {isBotMessage && (
        <div className="flex justify-center mt-2">
          <button onClick={() => handleYesNoClick('yes')} className="mx-2 py-1 px-3 bg-green-500 text-white rounded-md">Yes</button>
          <button onClick={() => handleYesNoClick('no')} className="mx-2 py-1 px-3 bg-red-500 text-white rounded-md">No</button>
        </div>
      )}
    </div>
  )
}

export default Message
