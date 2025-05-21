import { Base } from "@/types/types";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import ConfirmDialog from "../ConfirmDialog";
import './LeftSideBar.css'

interface LeftSideBarProps {
  bases: Base[];
  // searchTerm: string;
  setShowCreateModal: Dispatch<SetStateAction<boolean>>;
  selectedBase: string | null;
  // setSearchTerm: Dispatch<SetStateAction<string>>;
  setSelectedBase: Dispatch<SetStateAction<string | null>>;
  ondeleteBase: (base: Base) => void;
  onRenameKnowledgeBase: (base: Base, knowledgeBaseName: string) => void;
}

const LeftSideBar: React.FC<LeftSideBarProps> = ({
  bases,
  // searchTerm,
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
    setSelectedBase(bases[0]?.baseId || null);
  }, [bases]);

  const [isSettingsOpen, setSettingsOpen] = useState<boolean[]>([]);
  const [inputValues, setInputValues] = useState<string[]>([]);
  const [isEditOpen, setIsEditOpen] = useState<boolean[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
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
    <div className="k-left-container flex-flex-col gap-4 h-full">
      <div className="k-left-c-title">
        知识库列表
      </div>
      <div className="k-new-chat" onClick={() => setShowCreateModal(true)}>
        <div className="k-new-chat-icon"></div>
        <button className="k-new-chat-text">新建知识库</button>
      </div>
      {/* <div className="px-4 flex items-center justify-center h-[10%]">
        <button
          onClick={() => setShowCreateModal(true)}
          className="w-full  bg-indigo-500 text-white hover:bg-indigo-700 transition-colors rounded-full"
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
      </div> */}

      <div className="relative w-full">
        <input
          type="text"
          placeholder="搜索"
          className="k-search w-full px-[10px] py-[5px] rounded-[5px] border border-gray-300 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="size-4 absolute right-[10px] top-1/2 transform -translate-y-1/2 text-gray-400"
        >
          <path
            fillRule="evenodd"
            d="M10.5 3.75a6.75 6.75 0 1 0 0 13.5 6.75 6.75 0 0 0 0-13.5ZM2.25 10.5a8.25 8.25 0 1 1 14.59 5.28l4.69 4.69a.75.75 0 1 1-1.06 1.06l-4.69-4.69A8.25 8.25 0 0 1 2.25 10.5Z"
            clipRule="evenodd"
          />
        </svg>
      </div>

      <div className="overflow-scroll scrollbar-hide mt-2 h-full">
        {filteredBases.map((base, index) => (
          <div
            key={index}
            className={`flex p-2 justify-between mb-[8px] cursor-pointer ${
              selectedBase === base.baseId ? "k-chat-active" : "k-chat-inactive"
            }`}
          >
            <div
              className={`flex-1 flex w-full justify-between items-center ${base.baseId === "1"? "cursor-not-allowed":""}`}
              onClick={() => {
                if (base.baseId === "1") {
                  return;
                }
                return setSelectedBase(base.baseId);
              }}
            >
              <img className="k-chat-img" src={`https://picsum.photos/400/400?random=${index}`} />

              <div className="flex-1 flex relative">
                <div
                  className={`flex flex-col justify-between ml-[5px] text-gray-900 w-[80px] ${
                    selectedBase === base.baseId
                      ? "text-white text-lg"
                      : "text-base"
                  }`}
                >

                  <div
                    className={`${
                      selectedBase === base.baseId ? "chat-text-active" : "chat-text-inactive"
                    } whitespace-nowrap overflow-hidden`} title={base.name}
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
                  <div
                    className={`${
                      selectedBase === base.baseId ? "chat-text-active" : "chat-text-inactive"
                    }`}
                  >
                    {base.fileNumber} 个文件
                  </div>
                </div>
                {/* 重命名和删除 */}
                <div
                  className="k-chat-edit-icon flex items-center justify-center font-semibold cursor-pointer text-white"
                  onClick={() => toggleSettings(index)}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 16 16"
                    fill="#000000"
                    className={`size-3`}
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
