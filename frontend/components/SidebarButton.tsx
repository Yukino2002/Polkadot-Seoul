import React, { useState, Fragment, ChangeEvent, FormEvent } from 'react';
import { Dialog, Transition } from '@headlessui/react';

interface SidebarButtonProps {
  text: string;
  icon: JSX.Element;
  onSubmit: (value: string) => void;
}

export const SidebarButton: React.FC<SidebarButtonProps> = ({ text, icon, onSubmit }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');

  const closeModal = () => {
    setIsOpen(false);
  }

  const openModal = () => {
    setIsOpen(true);
  }

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    setInputValue(event.target.value);
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit(inputValue);
    setInputValue('');
    closeModal();
  }

  return (
    <>
      <button onClick={openModal} className='flex text-white flex-row justify-center items-center space-x-4 py-2 px-10 rounded hover:bg-[#1e1e1e]'>
        {icon}
        <span>{text}</span>
      </button>

      <Transition appear show={isOpen} as={Fragment}>
        <Dialog
          as="div"
          className="fixed inset-0 z-10 overflow-y-auto"
          onClose={closeModal}
        >
          <Dialog.Overlay className="fixed inset-0 bg-black opacity-30" />

          <div className="min-h-screen px-4 text-center">
            <Dialog.Title className="text-lg font-medium text-white">
              Enter your {text}
            </Dialog.Title>

            <div className="mt-4">
              <form onSubmit={handleSubmit}>
                <input
                  type="text"
                  value={inputValue}
                  onChange={handleChange}
                  className="rounded-lg px-3 py-2 text-black"
                  placeholder={`Enter your ${text}`}
                />
                <button 
                  type="submit" 
                  className="ml-2 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                  Submit
                </button>
              </form>
            </div>
          </div>
        </Dialog>
      </Transition>
    </>
  )
}
