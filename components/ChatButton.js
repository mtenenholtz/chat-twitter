function ChatButton(props) {
    return (
        <button 
            className="bg-purple-500 text-white py-2 px-4 rounded-md hover:bg-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-50"
            onClick={() => props.onClick()}
        >
            Chat
        </button>
    );
  }
  
  export default ChatButton;