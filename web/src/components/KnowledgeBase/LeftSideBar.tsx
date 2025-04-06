import { Base } from "@/types/types";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import ConfirmDialog from "../ConfirmDialog";

interface LeftSideBarProps {
  bases: Base[];
  searchTerm: string;
  setShowCreateModal: Dispatch<SetStateAction<boolean>>;
  selectedBase: string | null;
  setSelectedBase: Dispatch<SetStateAction<string | null>>;
  ondeleteBase: (base: Base) => void;
  onRenameKnowledgeBase: (base: Base, knowledgeBaseName: string) => void;
}

const LeftSideBar: React.FC<LeftSideBarProps> = ({
  bases,
  searchTerm,
  setShowCreateModal,
  selectedBase,
  setSelectedBase,
  ondeleteBase,
  onRenameKnowledgeBase,
}) => {
  useEffect(() => {
    setSettingsOpen(new Array(bases.length).fill(false));
    setIsEditOpen(new Array(bases.length).fill(false));
    setInputValues(bases.map((base) => base.name));
  }, [bases]);

  const [isSettingsOpen, setSettingsOpen] = useState<boolean[]>([]);
  const [inputValues, setInputValues] = useState<string[]>([]);
  const [isEditOpen, setIsEditOpen] = useState<boolean[]>([]);
  const [showConfirmDeleteBase, setShowConfirmDeleteBase] = useState<{
    index: number;
    base: Base;
  } | null>(null);

  // 过滤知识库
  const filteredBases = bases.filter((base) =>
    base.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDeleteBase = (base: Base, index: number) => {
    setShowConfirmDeleteBase({ index, base }); // 显示单个对话框
  };

  const confirmDeleteBase = () => {
    if (showConfirmDeleteBase) {
      ondeleteBase(showConfirmDeleteBase.base);
      toggleSettings(showConfirmDeleteBase.index); // 关闭设置面板
      setShowConfirmDeleteBase(null); // 关闭对话框
    }
  };

  const cancelDeleteBase = () => {
    if (showConfirmDeleteBase) {
      toggleSettings(showConfirmDeleteBase.index); // 关闭设置面板
      setShowConfirmDeleteBase(null); // 关闭对话框
    }
  };

  const toggleSettings = (index: number) => {
    setSettingsOpen(
      (prev) => prev.map((item, idx) => (idx === index ? !item : false)) // 只切换当前项
    );
  };

  const handleEditBase = (index: number) => {
    toggleSettings(index);
    setIsEditOpen(
      (prev) => prev.map((item, idx) => (idx === index ? !item : false)) // 只切换当前项
    );
  };

  const handleBlur = (base: Base, index: number) => {
    if (
      inputValues[index].trim() !== "" &&
      inputValues[index].trim() !== base.name
    ) {
      onRenameKnowledgeBase(base, inputValues[index]);
    } else {
      inputValues[index] = base.name;
    }
    setIsEditOpen(
      (prev) => prev.map((item, idx) => (idx === index ? !item : false)) // 只切换当前项
    );
  };

  const handleChange = (
    index: number,
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const newInputValues = [...inputValues];
    newInputValues[index] = e.target.value; // 更新输入框的值
    setInputValues(newInputValues); // 设置新的输入值
  };

  return (
    <div className="w-[20%] flex-flex-col gap-4 h-full">
      <div className="px-4 flex items-center justify-center h-[10%]">
        <button
          onClick={() => setShowCreateModal(true)}
          className="w-full py-2 px-4 bg-indigo-500 text-white hover:bg-indigo-700 transition-colors rounded-full"
        >
          <div className="flex items-center gap-2 cursor-pointer">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="size-5"
            >
              <path
                fillRule="evenodd"
                d="M12 3.75a.75.75 0 0 1 .75.75v6.75h6.75a.75.75 0 0 1 0 1.5h-6.75v6.75a.75.75 0 0 1-1.5 0v-6.75H4.5a.75.75 0 0 1 0-1.5h6.75V4.5a.75.75 0 0 1 .75-.75Z"
                clipRule="evenodd"
              />
            </svg>

            <span>Add Knowledge-Base</span>
          </div>
        </button>
      </div>

      <div className="bg-white rounded-2xl overflow-scroll min-h-[90%] max-h-[90%] scrollbar-hide p-2">
        {filteredBases.map((base, index) => (
          <div
            key={index}
            className={`py-2 my-2 hover:bg-indigo-200  cursor-pointer rounded-2xl flex justify-between items-start ${
              selectedBase === base.baseId ? "bg-indigo-500" : ""
            }`}
          >
            <div
              className={`flex-1 gap-2 hover:text-white w-full ${base.baseId === "1"? "cursor-not-allowed":""}`}
              onClick={() => {
                if (base.baseId === "1") {
                  return;
                }
                return setSelectedBase(base.baseId);
              }}
            >
              <div className="flex relative">
                <div
                  className={`px-3 flex items-center gap-2 text-gray-900 w-[80%] ${
                    selectedBase === base.baseId
                      ? "text-white text-lg"
                      : "text-base"
                  }`}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className={`${
                      selectedBase === base.baseId ? "size-6" : "size-5"
                    }  shrink-0`}
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 1c3.866 0 7 1.79 7 4s-3.134 4-7 4-7-1.79-7-4 3.134-4 7-4Zm5.694 8.13c.464-.264.91-.583 1.306-.952V10c0 2.21-3.134 4-7 4s-7-1.79-7-4V8.178c.396.37.842.688 1.306.953C5.838 10.006 7.854 10.5 10 10.5s4.162-.494 5.694-1.37ZM3 13.179V15c0 2.21 3.134 4 7 4s7-1.79 7-4v-1.822c-.396.37-.842.688-1.306.953-1.532.875-3.548 1.369-5.694 1.369s-4.162-.494-5.694-1.37A7.009 7.009 0 0 1 3 13.179Z"
                      clipRule="evenodd"
                    />
                  </svg>

                  <div
                    className={`${
                      selectedBase === base.baseId ? "text-lg" : "text-base"
                    } whitespace-nowrap overflow-hidden`}
                  >
                    {isEditOpen[index] ? (
                      <input
                        type="text"
                        value={inputValues[index]} // 使用状态中的输入值
                        onChange={(e) => handleChange(index, e)} // 更新输入值
                        onBlur={() => handleBlur(base, index)}
                        className="bg-transparent outline-hidden border-none p-0 m-0 w-full"
                        autoFocus
                      />
                    ) : (
                      base.name
                    )}
                  </div>
                </div>
                {/* 重命名和删除 */}
                <div
                  className="w-[20%] flex items-center justify-center font-semibold cursor-pointer text-white"
                  onClick={() => toggleSettings(index)}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    className={`${
                      selectedBase === base.baseId ? "size-6" : "size-5"
                    }`}
                  >
                    <path d="M2 8a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0ZM6.5 8a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0ZM12.5 6.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z" />
                  </svg>
                </div>
                {isSettingsOpen[index] && ( // 根据数组状态显示悬浮框
                  <div className="absolute right-0 top-full mt-1 bg-white text-black rounded-xl border-2 py-2 px-1 border-slate-200 shadow-lg z-10">
                    <div
                      className="flex gap-2 cursor-pointer hover:bg-indigo-500 hover:text-white px-2 py-1 rounded-lg"
                      onClick={() => handleEditBase(index)}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={1.5}
                        stroke="currentColor"
                        className="size-5"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125"
                        />
                      </svg>

                      <div className="text-sm">Rename</div>
                    </div>
                    <div
                      className="flex gap-2 cursor-pointer hover:bg-indigo-500 hover:text-white px-2 py-1 rounded-lg"
                      onClick={() => handleDeleteBase(base, index)}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={1.5}
                        stroke="currentColor"
                        className="size-5"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
                        />
                      </svg>
                      <div className="text-sm">Delete</div>
                    </div>
                  </div>
                )}
              </div>
              <p
                className={`px-4 text-sm text-gray-500 ${
                  selectedBase === base.baseId ? "text-white" : ""
                }`}
              >
                {base.fileNumber} files
              </p>
            </div>
          </div>
        ))}
      </div>
      {showConfirmDeleteBase && (
        <ConfirmDialog
          message={`Confirm the deletion of knowledge-base "${showConfirmDeleteBase.base.name}"？`}
          onConfirm={confirmDeleteBase}
          onCancel={cancelDeleteBase}
        />
      )}
    </div>
  );
};

export default LeftSideBar;
