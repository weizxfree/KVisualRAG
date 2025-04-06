"use client";
import AddKnowledgeBase from "@/components/KnowledgeBase/AddKnowledgeBase";
import KnowledgeBaseDetails from "@/components/KnowledgeBase/KnowledgeBaseDetails";
import LeftSideBar from "@/components/KnowledgeBase/LeftSideBar";
import TopBar from "@/components/KnowledgeBase/TopBar";
import Navbar from "@/components/NavbarComponents/Navbar";
import {
  createKnowledgeBase,
  deleteKnowledgeBase,
  getAllKnowledgeBase,
  renameKnowledgeBase,
  uploadFiles,
} from "@/lib/api/knowledgeBaseApi";
import withAuth from "@/middlewares/withAuth";
import { useAuthStore } from "@/stores/authStore";
import { Base, UploadFile } from "@/types/types";
import { getFileExtension } from "@/utils/file";
import { useState, useEffect, useCallback } from "react";
import Cookies from "js-cookie";
import { EventSourceParserStream } from "eventsource-parser/stream";

const KnowledgeBase = () => {
  const [selectedBase, setSelectedBase] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [bases, setBases] = useState<Base[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newBaseName, setNewBaseName] = useState("");
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [nameError, setNameError] = useState<string | null>(null);
  const { user } = useAuthStore();
  const [refresh, setRefresh] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(0);
  const [taskStatus, setTaskStatus] = useState<
    "processing" | "completed" | "failed" | null
  >(null);
  const [taskProgress, setTaskProgress] = useState<number>(0);
  const [uploadFile, setUploadFile] = useState<boolean>(false);
  const [load, setLoad] = useState(true);

  // 修改发送按钮逻辑
  const isUploadComplete = uploadProgress === 100;
  const isTaskComplete = taskStatus === "completed";
  const isSendDisabled = (!isUploadComplete || !isTaskComplete) && uploadFile;

  let buttonText;
  if (!uploadFile) {
    buttonText = "Upload Files";
  } else if (!isUploadComplete) {
    buttonText = `Upload:${uploadProgress}%`;
  } else if (!isTaskComplete) {
    buttonText =
      taskStatus === "failed" ? "Upload Failed" : `Processing:${taskProgress}%`;
  } else {
    buttonText = "Upload Files";
  }

  // 成功消息自动消失
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  // 支持的文件类型
  const supportedExtensions = ["pdf"];

  // Wrap fetchAllKnowledgeBase with useCallback
  const fetchAllKnowledgeBase = useCallback(async () => {
    if (user?.name) {
      try {
        const response = await getAllKnowledgeBase(user.name);
        const bases: Base[] = response.data.map((item: any) => ({
          name: item.knowledge_base_name,
          baseId: item.knowledge_base_id,
          lastModityTime: item.last_modify_at.split("T")[0],
          createTime: item.created_at.split("T")[0],
          fileNumber: item.file_number,
        }));
        setBases(bases);
      } catch (error) {
        console.error("Error fetching chat history:", error);
      }
    }
  }, [user?.name]); // Add dependencies

  useEffect(() => {
    fetchAllKnowledgeBase();
  }, [user?.name, refresh, fetchAllKnowledgeBase]); // Add fetchAllKnowledgeBase

  // 创建知识库校验
  const handleCreateConfirm = async () => {
    if (!newBaseName.trim()) {
      setNameError("Knowledge-Base name can not be null!");
      return;
    }
    if (bases.some((base) => base.name === newBaseName)) {
      setNameError("Knowledge-Base name already exist!");
      return;
    }

    if (user?.name) {
      try {
        setBases((prevBase: Base[]) => {
          return [
            {
              name: "加载中...",
              baseId: "1",
              lastModityTime: "加载中...",
              createTime: "加载中...",
              fileNumber: 0,
            },
            ...prevBase,
          ];
        });
        setShowCreateModal(false);
        setNewBaseName("");
        setNameError(null);
        const response = await createKnowledgeBase(user.name, newBaseName);
        setSelectedBase(null);
      } catch (error) {
        console.error("Error fetching chat history:", error);
      }
    }
    setRefresh((pre) => !pre);
  };

  // 删除知识库
  const handledeleteBase = async (base: Base) => {
    if (user?.name) {
      try {
        setBases((prevBase: Base[]) =>
          prevBase.filter((c: { baseId: string }) => c.baseId !== base.baseId)
        );
        const response = await deleteKnowledgeBase(base.baseId);
      } catch (error) {
        console.error("Error delete Knowledge Base:", error);
      }
      setSelectedBase(null);
      setRefresh((pre) => !pre);
    }
  };

  const handleRenameKnowledgeBase = (base: Base, inputValue: string) => {
    const fetchRenameChat = async () => {
      if (user?.name) {
        try {
          setBases((prevBase: Base[]) =>
            prevBase.map((c) =>
              c.baseId === base.baseId ? { ...c, name: inputValue } : c
            )
          );
          await renameKnowledgeBase(base.baseId, inputValue);
          setRefresh((prev) => !prev);
        } catch (error) {
          console.error("Error fetching rename chat:", error);
        }
      }
    };
    fetchRenameChat(); // 调用获取聊天记录的函数
  };

  const handleFileUpload = (filelist: FileList) => {
    const files = Array.from(filelist);
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

      if (user?.name && selectedBase) {
        uploadFiles(files, selectedBase, (percent) => {
          setUploadProgress(percent); // 更新上传进度
        })
          .then(async (response) => {
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
              setBases((prevBases) =>
                prevBases.map((base) =>
                  base.baseId === selectedBase
                    ? {
                        ...base,
                        fileNumber: base.fileNumber + validFiles.length,
                      }
                    : base
                )
              );
              setLoad((prev) => !prev);
            } catch (error) {
              console.error("SSE错误:", error);
              setTaskStatus("failed");
            }finally {
              setSelectedBase(null);
            }
          })
          .catch((error) => {
            alert("Upload error");
          });
      }
    }
  };

  return (
    <div className="overflow-hidden flex flex-col">
      <Navbar />
      <div className="absolute w-[96%] h-[91%] top-[7%] bg-white/10 left-[2%] rounded-3xl flex items-center justify-between shadow-2xl">
        <div className="w-full top-0 absolute px-6 pb-6 pt-2 h-full">
          {/* 新建知识库弹窗 */}
          {showCreateModal && (
            <AddKnowledgeBase
              setShowCreateModal={setShowCreateModal}
              nameError={nameError}
              setNameError={setNameError}
              newBaseName={newBaseName}
              setNewBaseName={setNewBaseName}
              onCreateConfirm={handleCreateConfirm}
            />
          )}

          {/* 成功提示 */}
          {successMessage && (
            <div className="w-[20%] text-center fixed top-[40%] left-[40%] bg-indigo-500 text-white px-4 py-2 rounded-lg shadow-lg animate-bounce">
              {successMessage}
            </div>
          )}

          {/* 顶部导航 */}
          <TopBar searchTerm={searchTerm} setSearchTerm={setSearchTerm} />

          <div className="mx-auto px-4 pt-4 flex gap-6 h-[88%]">
            {/* 左侧边栏 */}
            <LeftSideBar
              bases={bases}
              searchTerm={searchTerm}
              setShowCreateModal={setShowCreateModal}
              selectedBase={selectedBase}
              setSelectedBase={setSelectedBase}
              ondeleteBase={handledeleteBase}
              onRenameKnowledgeBase={handleRenameKnowledgeBase}
            />

            {/* 右侧内容区 */}
            <KnowledgeBaseDetails
              bases={bases}
              setBases={setBases}
              selectedBase={selectedBase}
              setSelectedBase={setSelectedBase}
              onFileUpload={handleFileUpload}
              buttonText={buttonText}
              isSendDisabled={isSendDisabled}
              load={load}
              setLoad={setLoad}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default withAuth(KnowledgeBase);
