import { Dispatch, SetStateAction } from "react";

interface TopBarProps {
  searchTerm: string;
  setSearchTerm: Dispatch<SetStateAction<string>>;
}

const TopBar: React.FC<TopBarProps> = ({ searchTerm, setSearchTerm }) => {
  return (
    <div className="bg-white shadow-xs rounded-xl flex items-center px-6 justify-between w-full h-[12%]">
      <div className="flex items-center gap-2">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="size-6"
        >
          <path d="M10.75 16.82A7.462 7.462 0 0 1 15 15.5c.71 0 1.396.098 2.046.282A.75.75 0 0 0 18 15.06v-11a.75.75 0 0 0-.546-.721A9.006 9.006 0 0 0 15 3a8.963 8.963 0 0 0-4.25 1.065V16.82ZM9.25 4.065A8.963 8.963 0 0 0 5 3c-.85 0-1.673.118-2.454.339A.75.75 0 0 0 2 4.06v11a.75.75 0 0 0 .954.721A7.506 7.506 0 0 1 5 15.5c1.579 0 3.042.487 4.25 1.32V4.065Z" />
        </svg>
        <h1 className="text-xl font-bold text-gray-800">My Knowledge-Base</h1>
      </div>
      <div className="relative w-[25%]">
        <input
          type="text"
          placeholder="Search Knowledge-Base..."
          className="w-full pl-6 pr-10 py-2 rounded-full border border-gray-300 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="size-6 absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400"
        >
          <path
            fillRule="evenodd"
            d="M10.5 3.75a6.75 6.75 0 1 0 0 13.5 6.75 6.75 0 0 0 0-13.5ZM2.25 10.5a8.25 8.25 0 1 1 14.59 5.28l4.69 4.69a.75.75 0 1 1-1.06 1.06l-4.69-4.69A8.25 8.25 0 0 1 2.25 10.5Z"
            clipRule="evenodd"
          />
        </svg>
      </div>
    </div>
  );
};

export default TopBar;
