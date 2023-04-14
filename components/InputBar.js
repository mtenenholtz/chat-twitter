import React, { useRef, useEffect } from 'react'

const InputBar = ({ input, setInput, handleKeyDown, handleSubmit }) => {
  const inputRef = useRef(null)

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = inputRef.current.scrollHeight + 'px'
    }
  }, [input])

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex items-center p-4 justify-center">
        <div className="w-1/3 flex items-center">
          <textarea
            ref={inputRef}
            rows="1"
            placeholder="Do likes impact the ranking of my tweets?"
            className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300 resize-none overflow-hidden bg-gray-600 text-gray-100"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            type="submit"
            className="ml-4 px-4 py-2 rounded-lg bg-blue-500 text-white focus:outline-none hover:bg-blue-600"
          >
            Send
          </button>
        </div>
      </form>
      <div className="pb-4 text-center text-xs text-gray-400">
        This is still a WIP, and answers may not be correct. Algorithm code last updated 2023-04-14.
      </div>
    </div>
  )
}

export default InputBar