'use client'
import { FunctionComponent, useState } from 'react';
import { ClipboardIcon, KeyIcon } from "@heroicons/react/24/solid";
import { SidebarButton } from "./SidebarButton"

interface CardProps {
  title: string;
  children: React.ReactNode;
}

const Card: FunctionComponent<CardProps> = ({ title, children }) => {
  return (
    <div className="rounded-lg bg-gray-700 p-4 mb-4">
      <h3 className="text-xl mb-2">{title}</h3>
      {children}
    </div>
  )
}

interface TransactionCardProps {
  amount: string;
  hash: string;
}

const TransactionCard: FunctionComponent<TransactionCardProps> = ({ amount, hash }) => {
  const url = `https://polkascan.io/polkadot/transaction/${hash}`;
  const displayedHash = `${hash.slice(0, 6)}...${hash.slice(-4)}`;
  return (
    <Card title="Last Transaction">
      <a href={url} target="_blank" rel="noopener noreferrer">
        <p>Amount: {amount}</p>
        <p>Hash: {displayedHash}</p>
      </a>
    </Card>
  )
}

const RightSidebar: FunctionComponent = () => {
  const walletBalance = "1000 DOT";
  const userAddress = "16ZL8yLyXv3V3L3z9ofR1ovFLziyXaN1DPq4yffMAZ9czzBD";
  const displayedUserAddress = `${userAddress.slice(0, 6)}...${userAddress.slice(-4)}`;
  const userAddressUrl = `https://polkascan.io/polkadot/account/${userAddress}`;

  const lastTransactionAmount = "50 DOT";
  const lastTransactionHash = "0xaa6a6b06c0a38b5239d13a2e700924ed1bbbaf44d5bbfdbb0a8adcef4d453f71";

  const copyToClipboard = () => {
    navigator.clipboard.writeText(userAddress);
  }

  const handleMnemonicKeySubmit = (value: string) => {
    console.log("Mnemonic Key: ", value);
    localStorage.setItem('mnemonicKey', value); // store the key in local storage
  }

  const handleOpenAIKeySubmit = (value: string) => {
    console.log("OpenAI API Key: ", value);
    localStorage.setItem('openAIKey', value); // store the key in local storage
  }

  return (
    <div className='text-white items-center p-2 flex flex-col h-screen'>
      <div className='flex-1'>
        {/* <p className='text-xl py-3'>Polkadot Information</p>
        <a href={userAddressUrl} target="_blank" rel="noopener noreferrer" className='flex'>
          <p className='text-l py-1 bg-gray-300/20 px-2 rounded '>Account Address: {displayedUserAddress} </p>
        </a>
        <p className='text-l py-1 bg-gray-300/20 px-2 rounded'>Wallet Balance: {walletBalance}</p>
        <br />
        <TransactionCard amount={lastTransactionAmount} hash={lastTransactionHash} /> */}
      </div>


      <div className="flex justify-center items-center py-2 border-t border-gray-500">
        {/* Mnemonic Key Input */}
        <SidebarButton
          text="Input Mnemonic Key"
          icon={<KeyIcon className="h-5 w-5" />}
          onSubmit={handleMnemonicKeySubmit} // use the new handler
        />
      </div>
      <div className="flex justify-center items-center py-2  border-gray-500 ">
        {/* OpenAI API Key Input */}
        <SidebarButton
          text="Input OpenAI API Key"
          icon={<KeyIcon className="h-5 w-5" />}
          onSubmit={handleOpenAIKeySubmit} // use the new handler
        />
      </div>
    </div>
  )
}

export default RightSidebar
