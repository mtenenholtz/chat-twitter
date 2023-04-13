'use client';

import { useState, useEffect, useRef } from 'react'

import Head from 'next/head'
import Header from '../components/Header'
import ChatMessages from '../components/ChatMessages'
import InputBar from '../components/InputBar'

export default function Home() {
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const inputRef = useRef(null)

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            handleSubmit(e)
        }
    }

    const getSystemMessage = async (userInputMessage) => {
        const response = await fetch('https://chat-twitter-backend.fly.dev:8080/system_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userInputMessage),
        })
        const systemMessage = await response.json();
        return { text: systemMessage.system_message, sender: 'systemMessage' }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()

        let updatedMessages = []
        if (input.trim()) {
            const userInputMessage = { text: input, sender: 'user' }
            if (messages.length === 0) {
                const systemMessage = await getSystemMessage(userInputMessage);
                console.log(systemMessage)
                updatedMessages = [systemMessage, userInputMessage];
            } else {
                updatedMessages = [...messages, userInputMessage]
            }
            setMessages(updatedMessages)

            await handleChat(updatedMessages)

            setInput('')
        }
    }

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = 'auto'
            inputRef.current.style.height = inputRef.current.scrollHeight + 'px'
        }
    }, [input])

    const handleChat = async (updatedMessages) => {
        let accumulatedText = "";

        fetch('https://chat-twitter-backend.fly.dev:8080/chat_stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updatedMessages),
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
            updatedMessages = [...updatedMessages, { text: '', sender: 'llm' }];
            setMessages(updatedMessages);
            const reader = stream.getReader();
            reader.read().then(function processText({ done, value }) {
                if (done) {
                    return;
                }
                setMessages((prevMessages) => {
                    let outputMessage = prevMessages[prevMessages.length - 1];
                    outputMessage.text = accumulatedText;
                    return [...prevMessages.slice(0, -1), outputMessage];
                });
                return reader.read().then(processText);
            });
        });
    };

  
return (
    <>
        <Head>
            <title>Chat With the Twitter Algorithm</title>
            <meta
                name="description"
                content="Chat with the Twitter algorithm."
            />
            <link rel="icon" href="/favicon.ico" />
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet" />
        </Head>
  
        <div className="h-screen flex flex-col bg-gray-800 text-gray-100 font-sans font-roboto">
            <Header />
            <div className="flex-1 overflow-auto p-4 flex justify-center">
                <ChatMessages messages={messages} />
            </div>
  
            <div className="border-t border-gray-700">
                <InputBar
                    input={input}
                    setInput={setInput}
                    handleKeyDown={handleKeyDown}
                    handleSubmit={handleSubmit}
                />
            </div>
      </div>
    </>
  )
}