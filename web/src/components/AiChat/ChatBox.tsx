// components/ChatBox.tsx
import React, { use, useEffect, useRef, useState } from "react";
import { BaseUsed, FileRespose, Message, ModelConfig } from "@/types/types";
import ChatMessage from "./ChatMessage";
import { getFileExtension, getFileIcon } from "@/utils/file";
import { uploadFiles } from "@/lib/api/chatApi";
import { useAuthStore } from "@/stores/authStore";
import KnowledgeConfigModal from "./KnowledgeConfigModal";
import useModelConfigStore from "@/stores/configStore";
import useChatStore from "@/stores/chatStore";
import Cookies from "js-cookie";
import { EventSourceParserStream } from "eventsource-parser/stream";
import { deleteFile } from "@/lib/api/knowledgeBaseApi";
import { updateModelConfig } from "@/lib/api/configApi";
import './ChatBox.css'

interface ChatBoxProps {
  messages: Message[];
  sendDisabled: boolean;
  onSendMessage: (
    message: string,
    files: FileRespose[],
    tempBaseId: string
  ) => void;
}

const ChatBox: React.FC<ChatBoxProps> = ({
  messages,
  onSendMessage,
  sendDisabled,
}) => {
  const [inputMessage, setInputMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null); // 创建引用
  const fileInputRef = useRef<HTMLInputElement>(null); // 新增文件输入引用
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [sendingFiles, setSendingFiles] = useState<FileRespose[]>([]);
  const [tempBaseId, setTempBaseId] = useState<string>(""); //后台用来存放上传文件的临时知识库
  const [fileDivStyle, setFileDivStyle] = useState({});
  const { user } = useAuthStore();
  const { modelConfig, setModelConfig } = useModelConfigStore();
  const [uploadProgress, setUploadProgress] = useState<number | null>(0);
  const [taskStatus, setTaskStatus] = useState<
    "processing" | "completed" | "failed" | null
  >(null);
  const [taskProgress, setTaskProgress] = useState<number>(0);
  const [uploadFile, setUploadFile] = useState<boolean>(false);
  const [showRefFile, setShowRefFile] = useState<string[]>([]);

  // 修改发送按钮逻辑
  const isUploadComplete = uploadProgress === 100;
  const isTaskComplete = taskStatus === "completed";
  const isSendDisabled = (!isUploadComplete || !isTaskComplete) && uploadFile;

  let buttonText;
  if (!uploadFile) {
    buttonText = "发送";
  } else if (!isUploadComplete) {
    buttonText = `上传:${uploadProgress}%`;
  } else if (!isTaskComplete) {
    buttonText =
      taskStatus === "failed" ? "上传失败" : `Processing:${taskProgress}%`;
  } else {
    buttonText = "发送";
  }

  // 在ChatBox组件内新增状态
  const [showConfigModal, setShowConfigModal] = useState(false);

  // 支持的文件类型
  const supportedExtensions = ["pdf"];

  const handleSend = () => {
    if (inputMessage.trim()) {
      // 发送用户消息
      onSendMessage(inputMessage, sendingFiles, tempBaseId);
      setInputMessage("");
      setSendingFiles([]);
      setTempBaseId("");
      setUploadFile(false);
      // 重置高度
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  // 使用 useEffect 监测 messages 的变化
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" }); // 平滑滚动到底部
    }
  }, [messages]);
  const { chatId, setChatId } = useChatStore();

  const configureKnowledgeDB = () => {
    setShowConfigModal(true);
  };

  // 新增保存配置方法
  const handleSaveConfig = async (config: ModelConfig) => {
    if (user?.name) {
      try {
        //更新数据库使用
        setModelConfig(config);
        await updateModelConfig(user.name, config);
      } catch (error) {
        console.error("保存配置失败:", error);
      }
    }
  };

  // 触发文件选择对话框
  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const handleDeleteFile = async (id: string) => {
    try {
      setSendingFiles((prevFiles) =>
        prevFiles.filter((file) => file.id !== id)
      );
      await deleteFile(tempBaseId, id);
    } catch (error) {
      console.error("Error delete file:", error);
    }
  };

  const handleFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles = files.filter((file) => {
      const ext = getFileExtension(file.name);
      return supportedExtensions.includes(ext);
    });

    const invalidFiles = files.filter((file) => {
      const ext = getFileExtension(file.name);
      return !supportedExtensions.includes(ext);
    });

    if (invalidFiles.length > 0) {
      alert(
        `Unsupport file type: \n${invalidFiles.map((f) => f.name).join("\n")}`
      );
    }

    if (validFiles.length > 0 && user?.name) {
      setUploadProgress(0); // 重置上传进度
      setTaskStatus(null); // 重置任务状态
      setUploadFile(true);

      uploadFiles(validFiles, user.name, chatId, (percent) => {
        setUploadProgress(percent); // 更新上传进度
      })
        .then(async (response) => {
          setSendingFiles((prev) => [...prev, ...response?.data.files]);
          setTempBaseId(response?.data.knowledge_db_id);

          // 使用fetch代替EventSource
          const token = Cookies.get("token"); // 确保已引入cookie库
          const taskId = response?.data.task_id;

          try {
            const response = await fetch(
              `${process.env.NEXT_PUBLIC_API_BASE_URL}/sse/task/${user.name}/${taskId}`,
              {
                headers: {
                  Authorization: `Bearer ${token}`,
                },
              }
            );

            if (!response.ok) throw new Error("Request failed");
            if (!response.body) return;

            // 使用EventSourceParserStream处理流
            const eventStream = response.body
              ?.pipeThrough(new TextDecoderStream())
              .pipeThrough(new EventSourceParserStream());

            const eventReader = eventStream.getReader();
            while (true) {
              const { done, value } = (await eventReader?.read()) || {};
              if (done) break;

              const payload = JSON.parse(value.data);
              // 处理事件数据
              if (payload.event === "progress") {
                const progress = payload.total > 0 ? payload.progress : 0;

                setTaskProgress(progress);
                setTaskStatus(payload.status);

                if (["completed", "failed"].includes(payload.status)) {
                  eventReader.cancel();
                  break;
                }
              }
            }
          } catch (error) {
            console.error("SSE错误:", error);
            setTaskStatus("failed");
          }
        })
        .catch((error) => {
          alert("Upload error");
        });
    }

    e.target.value = "";
  };

  const handleDownload = async (url: string) => {
    try {
      window.open(url, "_blank");
    } catch (error) {
      console.error("Download failed:", error);
      alert("Download failed!");
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      const height = textareaRef.current.getBoundingClientRect().height;
      setFileDivStyle({ bottom: `calc(55% + ${height}px/2` });
      // 如果需要，还可以设置 left 或其他样式属性
    }
  }, [inputMessage]); // 这个 effect 只在组件挂载时运行一次

  return (
    <div className="w-full chat-container h-full flex flex-col">
      <div className="flex-1 min-h-0 overflow-hidden">
        {messages.length === 0 ? (
          <div className="h-full w-[90%] flex flex-col items-center gap-4 bg-white/30 rounded-xl">
            <div className="h-[30vh]"></div>
            <p className="text-lg">
              {/* Please remember to choose which knowledge database you will use
              for this chat. */}
            </p>
            <button
              className="bg-indigo-500 hover:bg-indigo-600 rounded-full text-base px-4 py-2 text-white flex gap-1 cursor-pointer"
              onClick={configureKnowledgeDB}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="size-5 my-auto"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm.75-11.25a.75.75 0 0 0-1.5 0v2.5h-2.5a.75.75 0 0 0 0 1.5h2.5v2.5a.75.75 0 0 0 1.5 0v-2.5h2.5a.75.75 0 0 0 0-1.5h-2.5v-2.5Z"
                  clipRule="evenodd"
                />
              </svg>
              <div>配 置</div>
            </button>
            <div className="flex items-center justify-center gap-2 text-indigo-500 font-semibold">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="size-5"
              >
                <path
                  fillRule="evenodd"
                  d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25Zm0 8.625a1.125 1.125 0 1 0 0 2.25 1.125 1.125 0 0 0 0-2.25ZM15.375 12a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0ZM7.5 10.875a1.125 1.125 0 1 0 0 2.25 1.125 1.125 0 0 0 0-2.25Z"
                  clipRule="evenodd"
                />
              </svg>
              {modelConfig.modelName ? (
                <div className="text-indigo-500">{modelConfig.modelName}</div>
              ) : (
                <div className="text-indigo-500">No LLM engine was choosed</div>
              )}
            </div>
            {modelConfig.baseUsed.length > 0 ? (
              <div className="flex items-center justify-center w-full text-sm text-indigo-500 font-semibold gap-2">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="size-5"
                >
                  <path d="M10.75 16.82A7.462 7.462 0 0 1 15 15.5c.71 0 1.396.098 2.046.282A.75.75 0 0 0 18 15.06v-11a.75.75 0 0 0-.546-.721A9.006 9.006 0 0 0 15 3a8.963 8.963 0 0 0-4.25 1.065V16.82ZM9.25 4.065A8.963 8.963 0 0 0 5 3c-.85 0-1.673.118-2.454.339A.75.75 0 0 0 2 4.06v11a.75.75 0 0 0 .954.721A7.506 7.506 0 0 1 5 15.5c1.579 0 3.042.487 4.25 1.32V4.065Z" />
                </svg>
                <div className="whitespace-nowrap">
                  {" "}
                  知识库:
                </div>
                <div className="whitespace-nowrap overflow-x-scroll scrollbar-hide flex gap-2">
                  {modelConfig.baseUsed.map((base, index) => (
                    <div
                      className="flex gap-1 items-center justify-center"
                      key={index}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        className="size-4"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 1c3.866 0 7 1.79 7 4s-3.134 4-7 4-7-1.79-7-4 3.134-4 7-4Zm5.694 8.13c.464-.264.91-.583 1.306-.952V10c0 2.21-3.134 4-7 4s-7-1.79-7-4V8.178c.396.37.842.688 1.306.953C5.838 10.006 7.854 10.5 10 10.5s4.162-.494 5.694-1.37ZM3 13.179V15c0 2.21 3.134 4 7 4s7-1.79 7-4v-1.822c-.396.37-.842.688-1.306.953-1.532.875-3.548 1.369-5.694 1.369s-4.162-.494-5.694-1.37A7.009 7.009 0 0 1 3 13.179Z"
                          clipRule="evenodd"
                          transform="translate(0, -0.5)"
                        />
                      </svg>
                      <span>{base.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center w-full text-sm text-indigo-500 font-semibold gap-2">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="size-5"
                >
                  <path d="M10.75 16.82A7.462 7.462 0 0 1 15 15.5c.71 0 1.396.098 2.046.282A.75.75 0 0 0 18 15.06v-11a.75.75 0 0 0-.546-.721A9.006 9.006 0 0 0 15 3a8.963 8.963 0 0 0-4.25 1.065V16.82ZM9.25 4.065A8.963 8.963 0 0 0 5 3c-.85 0-1.673.118-2.454.339A.75.75 0 0 0 2 4.06v11a.75.75 0 0 0 .954.721A7.506 7.506 0 0 1 5 15.5c1.579 0 3.042.487 4.25 1.32V4.065Z" />
                </svg>
                <div className="whitespace-nowrap">
                  尚未配置知识库
                  {/* No Knowledge-Base was accessed‌ */}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="h-[100%] w-[70%] flex flex-col mx-auto">
            <div className="shadow-xs rounded-xl pt-1 pb-1 mb-2 flex flex-col item-center justify-center gap-1">
              <div className="w-full px-10 text-sm flex items-center justify-center gap-2 text-indigo-500 font-semibold">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="size-5"
                >
                  <path
                    fillRule="evenodd"
                    d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25Zm0 8.625a1.125 1.125 0 1 0 0 2.25 1.125 1.125 0 0 0 0-2.25ZM15.375 12a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0ZM7.5 10.875a1.125 1.125 0 1 0 0 2.25 1.125 1.125 0 0 0 0-2.25Z"
                    clipRule="evenodd"
                  />
                </svg>
                {modelConfig.modelName ? (
                  <div className="text-indigo-500 whitespace-nowrap overflow-x-scroll scrollbar-hide ">
                    {modelConfig.modelName}
                  </div>
                ) : (
                  <div className="text-indigo-500">
                    No LLM engine was choosed
                  </div>
                )}
              </div>
              {modelConfig.baseUsed.length > 0 ? (
                <div className="px-10 flex items-center justify-center w-full text-sm text-indigo-500 font-semibold gap-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="size-5"
                  >
                    <path d="M10.75 16.82A7.462 7.462 0 0 1 15 15.5c.71 0 1.396.098 2.046.282A.75.75 0 0 0 18 15.06v-11a.75.75 0 0 0-.546-.721A9.006 9.006 0 0 0 15 3a8.963 8.963 0 0 0-4.25 1.065V16.82ZM9.25 4.065A8.963 8.963 0 0 0 5 3c-.85 0-1.673.118-2.454.339A.75.75 0 0 0 2 4.06v11a.75.75 0 0 0 .954.721A7.506 7.506 0 0 1 5 15.5c1.579 0 3.042.487 4.25 1.32V4.065Z" />
                  </svg>
                  <div className="whitespace-nowrap">
                    {" "}
                    知识库:
                  </div>
                  <div className="whitespace-nowrap overflow-x-scroll scrollbar-hide flex gap-2">
                    {modelConfig.baseUsed.map((base, index) => (
                      <div
                        className="flex gap-1 items-center justify-center"
                        key={index}
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                          className="size-4"
                        >
                          <path
                            fillRule="evenodd"
                            d="M10 1c3.866 0 7 1.79 7 4s-3.134 4-7 4-7-1.79-7-4 3.134-4 7-4Zm5.694 8.13c.464-.264.91-.583 1.306-.952V10c0 2.21-3.134 4-7 4s-7-1.79-7-4V8.178c.396.37.842.688 1.306.953C5.838 10.006 7.854 10.5 10 10.5s4.162-.494 5.694-1.37ZM3 13.179V15c0 2.21 3.134 4 7 4s7-1.79 7-4v-1.822c-.396.37-.842.688-1.306.953-1.532.875-3.548 1.369-5.694 1.369s-4.162-.494-5.694-1.37A7.009 7.009 0 0 1 3 13.179Z"
                            clipRule="evenodd"
                            transform="translate(0, -0.5)"
                          />
                        </svg>
                        <span>{base.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="px-10 flex items-center justify-center w-full text-sm text-indigo-500 font-semibold gap-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="size-5"
                  >
                    <path d="M10.75 16.82A7.462 7.462 0 0 1 15 15.5c.71 0 1.396.098 2.046.282A.75.75 0 0 0 18 15.06v-11a.75.75 0 0 0-.546-.721A9.006 9.006 0 0 0 15 3a8.963 8.963 0 0 0-4.25 1.065V16.82ZM9.25 4.065A8.963 8.963 0 0 0 5 3c-.85 0-1.673.118-2.454.339A.75.75 0 0 0 2 4.06v11a.75.75 0 0 0 .954.721A7.506 7.506 0 0 1 5 15.5c1.579 0 3.042.487 4.25 1.32V4.065Z" />
                  </svg>
                  <div className="whitespace-nowrap">
                    尚未配置知识库
                    {/* No Knowledge-Base was accessed‌ */}
                  </div>
                </div>
              )}
            </div>
            <div
              className="flex-1 overflow-y-auto scrollbar-hide"
              style={{ overscrollBehavior: "contain" }}
            >
              {messages.map((message, index) => (
                <ChatMessage
                  key={index}
                  message={message}
                  showRefFile={showRefFile}
                  setShowRefFile={setShowRefFile}
                />
              ))}
              {/* 这个 div 用于滚动到底部 */}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}
      </div>
      {/* 新增定位容器 */}
      <div className="relative w-[70%] mt-4 mb-4 max-h-[25%] flex items-center justify-center gap-4 mx-auto">
        <div className="relative min-w-[75%] h-[100%]">
          <div className="flex justify-center items-center h-full">
            <textarea
              ref={textareaRef}
              className="pl-11 pr-8 w-full py-3 min-h-[40%] max-h-[100%] border-indigo-500 border-2 rounded-xl text-base focus:outline-hidden focus:border-indigo-600 focus:border-[2.5px] resize-none overflow-y-auto"
              placeholder="按 Shift+Enter 发送..."
              value={inputMessage}
              rows={1}
              onChange={(e) => {
                setInputMessage(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = e.target.scrollHeight + "px";
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && e.shiftKey) {
                  e.preventDefault();
                  if (!isSendDisabled || !sendDisabled) {
                    handleSend();
                  }
                }
              }}
            />
          </div>

          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="size-5 absolute right-3 top-1/2 transform -translate-y-1/2 cursor-pointer text-gray-400"
            onClick={() => {
              setInputMessage("");
              // 重置高度
              if (textareaRef.current) {
                textareaRef.current.style.height = "auto";
              }
            }} // 点击时清空输入框内容
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16ZM8.28 7.22a.75.75 0 0 0-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 1 0 1.06 1.06L10 11.06l1.72 1.72a.75.75 0 1 0 1.06-1.06L11.06 10l1.72-1.72a.75.75 0 0 0-1.06-1.06L10 8.94 8.28 7.22Z"
              clipRule="evenodd"
            />
          </svg>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className={`size-6 absolute left-3 top-1/2 transform -translate-y-1/2 ${
              isSendDisabled ? "cursor-not-allowed" : "cursor-pointer"
            }`}
            onClick={() => {
              if (!isSendDisabled) {
                return triggerFileInput();
              }
            }} // 点击时清空输入框内容
          >
            <path
              fillRule="evenodd"
              d="M18.97 3.659a2.25 2.25 0 0 0-3.182 0l-10.94 10.94a3.75 3.75 0 1 0 5.304 5.303l7.693-7.693a.75.75 0 0 1 1.06 1.06l-7.693 7.693a5.25 5.25 0 1 1-7.424-7.424l10.939-10.94a3.75 3.75 0 1 1 5.303 5.304L9.097 18.835l-.008.008-.007.007-.002.002-.003.002A2.25 2.25 0 0 1 5.91 15.66l7.81-7.81a.75.75 0 0 1 1.061 1.06l-7.81 7.81a.75.75 0 0 0 1.054 1.068L18.97 6.84a2.25 2.25 0 0 0 0-3.182Z"
              clipRule="evenodd"
            />
          </svg>
          <div className="text-xs absolute left-[calc(12px+18px)] top-[calc(50%+10px)] transform -translate-y-1/2">
            {sendingFiles.length}
          </div>
          {/* 隐藏的文件输入 */}
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            multiple
            accept=".pdf"
            onChange={handleFileSelected}
          />
          <div
            className="flex-col gap-1 absolute left-[1%]"
            style={fileDivStyle}
          >
            {sendingFiles &&
              sendingFiles.map((file, index) => (
                <div
                  className="w-full overflow-hidden flex gap-1 mt-1 text-xs bg-white rounded-xl"
                  key={index}
                >
                  <span>{getFileIcon(getFileExtension(file.filename))}</span>
                  <span
                    onClick={() => handleDownload(file.url ? file.url : "")}
                    className="hover:text-indigo-500 hover:cursor-pointer"
                  >
                    {file.filename}
                  </span>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth="1.5"
                    stroke="currentColor"
                    className={`size-4 text-indigo-500 hover:text-indigo-700 ${
                      isSendDisabled ? "cursor-not-allowed" : "cursor-pointer"
                    }`}
                    onClick={() => {
                      if (!isSendDisabled) {
                        return handleDeleteFile(file.id);
                      }
                    }}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M6 18 18 6M6 6l12 12"
                    />
                  </svg>
                </div>
              ))}
          </div>
        </div>
        <button
          className={`min-w-[14%] flex gap-1 ${
            isSendDisabled || sendDisabled
              ? "bg-indigo-300 cursor-not-allowed"
              : "bg-indigo-500 hover:bg-indigo-600"
          } rounded-full text-base item-center justify-center px-5 py-2 text-white`}
          onClick={handleSend}
          disabled={isSendDisabled || sendDisabled}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="size-6"
          >
            <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
          </svg>
          {buttonText}
        </button>
      </div>
      <KnowledgeConfigModal
        visible={showConfigModal}
        setVisible={setShowConfigModal}
        onSave={handleSaveConfig}
      />
    </div>
  );
};

export default ChatBox;
