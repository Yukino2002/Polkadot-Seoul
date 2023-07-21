import { DocumentData } from "firebase/firestore";

type Props = {
  message: DocumentData,
  isBotMessage: boolean,
  isFlag: boolean,
}

const botAvatar = "https://i.imgur.com/usI3OTw.png"; 

const Message = ({
  message,
  isBotMessage,
  isFlag,
}: Props) => {
  console.log(message)

  const handleYesNoClick = (choice: string) => {
    console.log(`User selected: ${choice}`);
    if (isFlag) {
      console.log("Executing flag-specific code...");
      // Add your flag-specific code here
    }
  }

  return (
    <div className={`py-5 text-white ${isBotMessage ? 'bg-gray-300/10' : ''}`}> {/* add gray background if it's a bot's message */}
      <div className="flex space-x-5 px-10 max-2-2xl mx-auto">
        <img src={isBotMessage ? botAvatar : message.user.avatar} alt="" className="h-8 w-8" /> {/* use botAvatar if it's a bot's message */}
        <p className="pt-1 text-sm">
          {message.text}
        </p>
      </div>
      {isBotMessage && isFlag && (
        <div className="flex justify-center mt-2">
          <button onClick={() => handleYesNoClick('yes')} className="mx-2 py-1 px-3 bg-green-500 text-white rounded-md">Yes</button>
          <button onClick={() => handleYesNoClick('no')} className="mx-2 py-1 px-3 bg-red-500 text-white rounded-md">No</button>
        </div>
      )}
    </div>
  )
}

export default Message
