import { Dispatch, SetStateAction } from "react";

interface AddKnowledgeBaseProps {
  setShowCreateModal: Dispatch<SetStateAction<boolean>>;
  nameError: string | null;
  setNameError: Dispatch<SetStateAction<string | null>>;
  newBaseName: string;
  setNewBaseName: Dispatch<SetStateAction<string>>;
  onCreateConfirm:() => void;
}

const AddKnowledgeBase: React.FC<AddKnowledgeBaseProps> = ({
  setShowCreateModal,
  nameError,
  setNameError,
  newBaseName,
  setNewBaseName,
  onCreateConfirm,
}) => {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl p-6 w-[35%]">
        <div className="flex items-center gap-2 mb-6">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="size-5"
          >
            <path d="M10.75 16.82A7.462 7.462 0 0 1 15 15.5c.71 0 1.396.098 2.046.282A.75.75 0 0 0 18 15.06v-11a.75.75 0 0 0-.546-.721A9.006 9.006 0 0 0 15 3a8.963 8.963 0 0 0-4.25 1.065V16.82ZM9.25 4.065A8.963 8.963 0 0 0 5 3c-.85 0-1.673.118-2.454.339A.75.75 0 0 0 2 4.06v11a.75.75 0 0 0 .954.721A7.506 7.506 0 0 1 5 15.5c1.579 0 3.042.487 4.25 1.32V4.065Z" />
          </svg>
          <h3 className="text-lg font-medium">New Knowledge-Base</h3>
        </div>
        <div className="px-4 w-full">
          <input
            type="text"
            placeholder="Write your knowledge base name..."
            className={`w-full px-4 py-2 mb-2 border border-gray-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-indigo-500 ${
              nameError ? "border-red-500" : "border-gray-300"
            }`}
            value={newBaseName}
            onChange={(e) => {
              setNewBaseName(e.target.value);
              setNameError(null);
            }}
            onKeyDown = {(e: React.KeyboardEvent) => {
              if (e.key === "Enter") {
                e.preventDefault(); // 防止默认回车行为
                onCreateConfirm();
              }
            }}
            autoFocus
          />
          {nameError && (
            <p className="text-red-500 text-sm mb-2 px-2">{nameError}</p>
          )}
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <button
            onClick={() => setShowCreateModal(false)}
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded-full hover:bg-gray-100 cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={onCreateConfirm}
            className="px-4 py-2 text-white bg-indigo-500 rounded-full hover:bg-indigo-700 cursor-pointer"
          >
            Yes
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddKnowledgeBase;
