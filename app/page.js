'use client';

import "@/app/globals.css";

import { useState } from 'react';

import Image from 'next/image'
import { Inter } from 'next/font/google'
import Head from 'next/head';

import TextInput from '../components/TextInput'
import TextOutput from '../components/TextOutput'
import ChatButton from '../components/ChatButton'

const inter = Inter({ subsets: ['latin'] })

export default function Home() {
  const [inputTextValue, setInputTextValue] = useState('');
  const [outputTextValue, setOutputTextValue] = useState('');

  const handleChat = async () => {
    if (!inputTextValue) {
      alert('Enter some text.');
      return;
    }

    setOutputTextValue("");
    let accumulatedText = "";

    fetch('http://localhost:8000/chat_stream/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            text: inputTextValue
          }),
        })
      .then(response => {
        const reader = response.body.getReader();
        return new ReadableStream({
          async start(controller) {
            while (true) {
              const { done, value } = await reader.read();
              if (done) {
                break;
              }
              let newToken = new TextDecoder().decode(value);
              accumulatedText += newToken;
              controller.enqueue(newToken);
            }
            controller.close();
            reader.releaseLock();
          }
        });
      })
      .then(stream => {
        const reader = stream.getReader();
        reader.read().then(function processText({ done, value }) {
          if (done) {
            return;
          }
          setOutputTextValue(accumulatedText);
          return reader.read().then(processText);
        });
      });
  };
  
  return (
    <>
      <Head>
        <title>Chat With the Algorithm</title>
        <meta
          name="description"
          content="Chat with the Twitter algorithm."
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="flex h-full min-h-screen flex-col items-center bg-[#00092b] px-4 pb-20 text-neutral-200 sm:px-10">

        <div className="mt-10 flex flex-col items-center justify-center sm:mt-20">
          <div className="text-4xl font-bold">Chat With the Algorithm</div>
        </div>

        <div className="mt-6 text-center text-sm w-1/3 h-32">
          <TextInput
            id='userInput'
            value={inputTextValue}
            onChange={setInputTextValue}
          />
        </div>
        
        <div className="mt-6 text-sm w-1/3 h-auto whitespace-pre-line">
          <TextOutput
            id='textOutput'
            value={outputTextValue}
          />
        </div>

        <div className="mt-6 text-center text-sm w-1/3 h-32">
          <ChatButton
            id='chatButton'
            onClick={handleChat}
          />
        </div>
        
      </div>
    </>
  )
}
