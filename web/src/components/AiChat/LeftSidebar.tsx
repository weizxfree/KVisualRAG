// components/Sidebar.tsx
import React, { useEffect, useRef, useState } from "react";
import { Chat } from "@/types/types";
import useChatStore from "@/stores/chatStore";
import { getTimeLabel } from "@/utils/date";
import ConfirmDialog from "../ConfirmDialog";
import { useClickAway } from "react-use";

interface SidebarProps {
  onNewChat: () => void;
  chatHistory: Chat[];
  onSelectChat: (inputChatId: string, isRead: boolean) => void;
  ondeleteAllChat: (chatHistory: Chat[]) => void;
  ondeleteChat: (chat: Chat) => void;
  onRenameChat: (chat: Chat, inputValue: string) => void;
}

const LeftSidebar: React.FC<SidebarProps> = ({
  onNewChat,
  chatHistory,
  onSelectChat,
  ondeleteAllChat,
  ondeleteChat,
  onRenameChat,
}) => {
  const [isSettingsOpen, setSettingsOpen] = useState<boolean[]>([]);
  const [isEditOpen, setIsEditOpen] = useState<boolean[]>([]);
  const [inputValues, setInputValues] = useState<string[]>([]);
  const [showConfirmDeleteAll, setShowConfirmDeleteAll] =
    useState<boolean>(false);
  const [showConfirmDeleteChat, setShowConfirmDeleteChat] = useState<{
    index: number;
    chat: Chat;
  } | null>(null);
  const { chatId } = useChatStore();

  const ref = useRef(null);
  useClickAway(ref, () => {
    setSettingsOpen((prev) => prev.map(() => false));
  });

  // 更新 isSettingsOpen 以匹配 chatHistory 的长度
  useEffect(() => {
    setSettingsOpen(new Array(chatHistory.length).fill(false));
    setIsEditOpen(new Array(chatHistory.length).fill(false));
    setInputValues(chatHistory.map((chat) => chat.name));
  }, [chatHistory]);

  const handleDeleteAllChats = () => {
    setShowConfirmDeleteAll(true); // 显示全局确认对话框
  };

  const handleDeleteChat = (chat: Chat, index: number) => {
    setShowConfirmDeleteChat({ index, chat }); // 显示单个对话框
  };

  const confirmDeleteAll = () => {
    ondeleteAllChat(chatHistory);
    setShowConfirmDeleteAll(false); // 关闭对话框
  };

  const cancelDeleteAll = () => {
    setShowConfirmDeleteAll(false); // 关闭对话框
  };

  const confirmDeleteChat = () => {
    if (showConfirmDeleteChat) {
      ondeleteChat(showConfirmDeleteChat.chat);
      toggleSettings(showConfirmDeleteChat.index); // 关闭设置面板
      setShowConfirmDeleteChat(null); // 关闭对话框
    }
  };

  const cancelDeleteChat = () => {
    if (showConfirmDeleteChat) {
      toggleSettings(showConfirmDeleteChat.index); // 关闭设置面板
      setShowConfirmDeleteChat(null); // 关闭对话框
    }
  };

  const toggleSettings = (index: number) => {
    setSettingsOpen(
      (prev) => prev.map((item, idx) => (idx === index ? !item : false)) // 只切换当前项
    );
  };

  const handleEditChat = (index: number) => {
    toggleSettings(index);
    setIsEditOpen(
      (prev) => prev.map((item, idx) => (idx === index ? !item : false)) // 只切换当前项
    );
  };

  const handleBlur = (chat: Chat, index: number) => {
    if (
      inputValues[index].trim() !== "" &&
      inputValues[index].trim() !== chat.name
    ) {
      onRenameChat(chat, inputValues[index]);
      //renameChat(chat.conversationId, inputValues[index]);
    } else {
      inputValues[index] = chat.name;
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

  const handleSelectChat = (chat: Chat) => {
    onSelectChat(chat.conversationId, chat.isRead);
  };

  return (
    <div className="bg-white/90 w-[20%] h-full rounded-3xl flex flex-col items-center p-2">
      {/* 新会话按钮 */}
      <div
        className="my-2 rounded-xl flex items-center justify-center w-full h-[8%] cursor-pointer"
        onClick={onNewChat}
      >
        <div className="gap-2 text-white px-5 py-2 bg-indigo-500 hover:bg-indigo-600 rounded-full flex items-center justify-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="size-5"
          >
            <path d="M3.505 2.365A41.369 41.369 0 0 1 9 2c1.863 0 3.697.124 5.495.365 1.247.167 2.18 1.108 2.435 2.268a4.45 4.45 0 0 0-.577-.069 43.141 43.141 0 0 0-4.706 0C9.229 4.696 7.5 6.727 7.5 8.998v2.24c0 1.413.67 2.735 1.76 3.562l-2.98 2.98A.75.75 0 0 1 5 17.25v-3.443c-.501-.048-1-.106-1.495-.172C2.033 13.438 1 12.162 1 10.72V5.28c0-1.441 1.033-2.717 2.505-2.914Z" />
            <path d="M14 6c-.762 0-1.52.02-2.271.062C10.157 6.148 9 7.472 9 8.998v2.24c0 1.519 1.147 2.839 2.71 2.935.214.013.428.024.642.034.2.009.385.09.518.224l2.35 2.35a.75.75 0 0 0 1.28-.531v-2.07c1.453-.195 2.5-1.463 2.5-2.915V8.998c0-1.526-1.157-2.85-2.729-2.936A41.645 41.645 0 0 0 14 6Z" />
          </svg>
          <div className=" text-sm">New Chat</div>
        </div>
      </div>

      {/* 历史生成标题和清空按钮 */}
      <h2 className="text-sm mb-2 text-center font-bold">History Chat</h2>
      <div className="flex gap-2">
        <div
          className="text-indigo-500 cursor-pointer flex gap-1 items-center"
          onClick={handleDeleteAllChats} // 修正这里
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="size-5"
          >
            <path d="M2 3a1 1 0 0 0-1 1v1a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1H2Z" />
            <path
              fillRule="evenodd"
              d="M2 7.5h16l-.811 7.71a2 2 0 0 1-1.99 1.79H4.802a2 2 0 0 1-1.99-1.79L2 7.5Zm5.22 1.72a.75.75 0 0 1 1.06 0L10 10.94l1.72-1.72a.75.75 0 1 1 1.06 1.06L11.06 12l1.72 1.72a.75.75 0 1 1-1.06 1.06L10 13.06l-1.72 1.72a.75.75 0 0 1-1.06-1.06L8.94 12l-1.72-1.72a.75.75 0 0 1 0-1.06Z"
              clipRule="evenodd"
            />
          </svg>

          <div>Clear</div>
        </div>
        <div
          className="text-gray-500 cursor-pointer flex items-center gap-1"
          onClick={onNewChat} // 修正这里
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="size-5"
          >
            <path
              fillRule="evenodd"
              d="M4.755 10.059a7.5 7.5 0 0 1 12.548-3.364l1.903 1.903h-3.183a.75.75 0 1 0 0 1.5h4.992a.75.75 0 0 0 .75-.75V4.356a.75.75 0 0 0-1.5 0v3.18l-1.9-1.9A9 9 0 0 0 3.306 9.67a.75.75 0 1 0 1.45.388Zm15.408 3.352a.75.75 0 0 0-.919.53 7.5 7.5 0 0 1-12.548 3.364l-1.902-1.903h3.183a.75.75 0 0 0 0-1.5H2.984a.75.75 0 0 0-.75.75v4.992a.75.75 0 0 0 1.5 0v-3.18l1.9 1.9a9 9 0 0 0 15.059-4.035.75.75 0 0 0-.53-.918Z"
              clipRule="evenodd"
            />
          </svg>

          <div>Refresh</div>
        </div>
      </div>
      {/* 聊天列表 */}
      <div className="border-b-2 border-gray-200 h-[1%] w-[80%]"></div>
      <div className="px-2 w-full flex-1 overflow-auto scrollbar-hide mt-2">
        {chatHistory.map((chat, index) => {
          const timeLabel = getTimeLabel(chat.lastModityTime);
          const lastTimeLabel = getTimeLabel(
            index === 0
              ? chat.lastModityTime
              : chatHistory[index - 1].lastModityTime
          );
          const isFirstInGroup = index === 0 || timeLabel !== lastTimeLabel;
          return (
            <div key={index} className="flex flex-col">
              {isFirstInGroup && (
                <div className="pl-2 py-2 font-bold text-sm">{timeLabel} </div>
              )}
              <div
                key={index}
                className={`relative flex ${
                  chatId === chat.conversationId
                    ? "bg-indigo-500 text-white"
                    : ""
                } hover:bg-indigo-300 hover:text-white rounded-xl`}
              >
                <div
                  key={index}
                  className="py-2 pl-2 pr-0 flex items-center gap-1 w-[80%] cursor-pointer text-md"
                  onClick={() => handleSelectChat(chat)}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className={`${
                      chatId === chat.conversationId ? "size-6" : "size-4"
                    } shrink-0`}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 0 1 .865-.501 48.172 48.172 0 0 0 3.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z"
                    />
                  </svg>

                  <div
                    className={`${
                      chatId === chat.conversationId ? "text-base" : "text-sm"
                    } whitespace-nowrap overflow-hidden `}
                  >
                    {isEditOpen[index] ? (
                      <input
                        type="text"
                        value={inputValues[index]} // 使用状态中的输入值
                        onChange={(e) => handleChange(index, e)} // 更新输入值
                        onBlur={() => handleBlur(chat, index)}
                        className="bg-transparent outline-hidden border-none p-0 m-0 w-full"
                        autoFocus
                      />
                    ) : (
                      chat.name.slice(0, 30)
                    )}
                  </div>
                </div>
                <div
                  className="w-[20%] flex items-center justify-center font-semibold cursor-pointer text-white"
                  onClick={() => toggleSettings(index)}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    className="size-4"
                  >
                    <path d="M2 8a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0ZM6.5 8a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0ZM12.5 6.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z" />
                  </svg>
                </div>
                {isSettingsOpen[index] && ( // 根据数组状态显示悬浮框
                  <div
                    ref={ref}
                    className="absolute right-0 top-full mt-1 bg-white text-black rounded-xl border-2 py-2 px-1 border-slate-200 shadow-lg z-10"
                  >
                    <div
                      className="flex gap-2 cursor-pointer hover:bg-indigo-500 hover:text-white px-2 py-1 rounded-lg"
                      onClick={() => handleEditChat(index)}
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
                      onClick={() => handleDeleteChat(chat, index)}
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
          );
        })}
      </div>

      {/* 确认删除所有聊天 */}
      {showConfirmDeleteAll && (
        <ConfirmDialog
          message="Confirm the deletion of all chat records?"
          onConfirm={confirmDeleteAll}
          onCancel={cancelDeleteAll}
        />
      )}

      {/* 确认删除单个聊天 */}
      {showConfirmDeleteChat && (
        <ConfirmDialog
          message={`Confirm the deletion of chat record "${showConfirmDeleteChat.chat.name.slice(
            0,
            30
          )}"？`}
          onConfirm={confirmDeleteChat}
          onCancel={cancelDeleteChat}
        />
      )}
    </div>
  );
};

export default LeftSidebar;
