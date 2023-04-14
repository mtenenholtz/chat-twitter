import React from 'react';

const Header = () => {
  return (
    <div className="bg-gray-700 text-white text-center py-4">
      <h1 className="text-2xl font-semibold">Chat With the Algorithm</h1>
      <div className="pt-2 text-center text-xs text-gray-400">
        <a
          href="https://github.com/twitter/the-algorithm"
          target="_blank"
          rel="noopener noreferrer"
        >
          https://github.com/twitter/the-algorithm
        </a>
      </div>
    </div>
  );
};

export default Header;