'use client'
import { KeyIcon } from "@heroicons/react/24/solid";
import { SidebarButton } from "./SidebarButton"


const RightSidebar = () => {
  return (
    <div className='text-white  items-center p-2 flex flex-col h-screen'>
        <div className='flex-1'>
            <p className='text-xl py-3'>Polkadot Information</p>
        </div>

        <div className="flex justify-center items-center py-2 border-t border-gray-500">
        {/* Mnemonic Key Input */}
        <SidebarButton
            text="Input Mnemonic Key"
            icon={<KeyIcon className="h-5 w-5"/>}
            onSubmit={(value) => {
                console.log("Mnemonic Key: ", value);
            }}
        />
        </div>

        <div className="flex justify-center items-center py-2  border-gray-500 ">
        {/* OpenAI API Key Input */}
        <SidebarButton
            text="Input OpenAI API Key"
            icon={<KeyIcon className="h-5 w-5"/>}
            onSubmit={(value) => {
                console.log("OpenAI API Key: ", value);
            }}
        />
        </div>
        
    </div>
  )
}

export default RightSidebar