import React from 'react'

const ChatMessages = ({ messages }) => {
  const filteredMessages = messages.filter(
    (message) => !(message.sender !== 'user' && message.text.length === 0)
  );

  return (
    <div className="w-1/3 flex flex-col">
      {filteredMessages.map((message, index) => (
        <div
          key={index}
          className={`mb-4 p-3 text-lg rounded-lg shadow-md whitespace-pre-line ${
            message.sender === 'user' ? 'bg-gray-100 text-gray-800' : 'bg-gray-600'
          }`}
        >
          {message.text}
        </div>
      ))}
    </div>
  )
}

export default ChatMessages