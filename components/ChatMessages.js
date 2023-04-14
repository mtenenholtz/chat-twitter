import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const ChatMessages = ({ messages }) => {
  const [fileData, setFileData] = useState([]);

  const filteredMessages = messages.filter(
    (message) =>
      !(message.sender === 'systemMessage' | (message.sender !== 'user' && message.text.length === 0)),
  );

  const formatMessage = (text) => {
    const codeBlockRegex = /(```[\w]*[\s\S]+?```)/g;
    const parts = text.split(codeBlockRegex);
  
    return parts.map((part, index) => {
      if (codeBlockRegex.test(part)) {
        const languageRegex = /```(\w*)\n/;
        const languageMatch = part.match(languageRegex);
        const language = languageMatch && languageMatch[1] ? languageMatch[1] : '';
  
        return (
          <SyntaxHighlighter
            key={index}
            language={language}
            style={oneDark}
            customStyle={{ backgroundColor: '#2d2d2d', borderRadius: '0.375rem', padding: '1rem' }}
          >
            {part.replace(languageRegex, '').replace(/```$/, '')}
          </SyntaxHighlighter>
        );
      } else {
        return (
          <span
            key={index}
            dangerouslySetInnerHTML={{
              __html: replaceFileNamesWithLinks(part, fileData),
            }}
          />
        );
      }
    });
  };

  useEffect(() => {
    async function fetchData() {
      const response = await fetch('api/fetchCsvData', {
          headers: {
            'Content-Type': 'application/json',
          },
      })
      .catch((error) => {
        console.log(error)
      });
      const data = await response.json();
      setFileData(data);
    };
    fetchData();
  }, []);

  const replaceFileNamesWithLinks = (text, data) => {
    const filenameRegex = /`?([\w-_/.]+)`?/g;
    return text.replace(filenameRegex, (match, filename) => {
      const fileExists = data.some((record) => record.file_name === filename);
      if (fileExists) {
        const url = `https://github.com/twitter/the-algorithm/blob/main/${filename}`;
        return `<a class="text-blue-500 underline cursor-pointer" href="${url}" target="_blank" rel="noopener noreferrer">${filename}</a>`;
      }
      return filename;
    });
  };

  return (
    <div className="w-1/3">
      {filteredMessages.map((message, index) => (
        <div
          key={index}
          className={`mb-4 p-3 text-lg rounded-lg shadow-md whitespace-pre-wrap ${
            message.sender === 'user' ? 'bg-gray-100 text-gray-800' : 'bg-gray-600'
          }`}
        >
          {formatMessage(message.text)}
        </div>
      ))}
    </div>
  );
};

export default ChatMessages;