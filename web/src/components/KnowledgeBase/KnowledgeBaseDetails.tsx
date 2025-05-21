import {
  deleteFile,
  getKBFiles,
  getUserFiles,
} from "@/lib/api/knowledgeBaseApi";
import { useAuthStore } from "@/stores/authStore";
import { Base, KnowledgeFile, UploadFile } from "@/types/types";
import {
  Dispatch,
  SetStateAction,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import ShowFiles from "./ShowFiles";

interface KnowledgeBaseDetailsProps {
  bases: Base[];
  setBases: Dispatch<SetStateAction<Base[]>>;
  selectedBase: string | null;
  setSelectedBase: Dispatch<SetStateAction<string | null>>;
  onFileUpload: (files: FileList) => void;
  buttonText: string;
  isSendDisabled: boolean;
  load: boolean;
  setLoad: Dispatch<SetStateAction<boolean>>;
}

const KnowledgeBaseDetails: React.FC<KnowledgeBaseDetailsProps> = ({
  bases,
  setBases,
  selectedBase,
  setSelectedBase,
  onFileUpload,
  buttonText,
  isSendDisabled,
  load,
  setLoad,
}) => {
  // 拖放处理
  const [dragActive, setDragActive] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [totalFiles, setTotalFiles] = useState(0);
  const { user } = useAuthStore();
  // 在组件顶部声明 ref（如果是函数组件）
  // 为每个搜索框创建独立 ref
  const search1Ref = useRef<HTMLInputElement>(null);
  const search2Ref = useRef<HTMLInputElement>(null);
  const loadFiles = useCallback(async () => {
    if (!user?.name) return;
    try {
      let response;
      if (selectedBase && selectedBase != "1") {
        response = await getKBFiles(
          selectedBase,
          currentPage,
          pageSize,
          searchKeyword
        );
      } else {
        response = await getUserFiles(
          user.name,
          currentPage,
          pageSize,
          searchKeyword
        );
      }
      setFiles(response.data.data);
      setTotalFiles(response.data.total);
    } catch (error) {
      console.error("Error loading files:", error);
    }
  }, [currentPage, searchKeyword, pageSize, user?.name, selectedBase]);

  useEffect(() => {
    loadFiles();
  }, [loadFiles]);

  useEffect(() => {
    if (searchKeyword === "") {
      setLoad((prev) => !prev);
      setCurrentPage(1);
    } else {
      setSearchKeyword("");
      setCurrentPage(1);
    }
  }, [selectedBase, setLoad]);

  const handleSearch = (value: string) => {
    setSearchKeyword(value);
    setCurrentPage(1); // 搜索时重置页码
  };

  const handleDeleteFile = async (file: KnowledgeFile) => {
    try {
      setFiles((prevFiles) =>
        prevFiles.filter((pre_file) => pre_file.file_id !== file.file_id)
      );
      setBases((prevBases) =>
        prevBases.map((base) =>
          base.baseId === file.kb_id
            ? { ...base, fileNumber: Math.max(0, base.fileNumber - 1) } // 防止负数
            : base
        )
      );
      await deleteFile(file.kb_id, file.file_id);
    } catch (error) {
      console.error("Error delete file:", error);
    }
  };

  const handleDownload = async (file: KnowledgeFile) => {
    try {
      window.open(file.url, "_blank");
    } catch (error) {
      console.error("Download failed:", error);
      alert("Download failed!");
    }
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      if (e.dataTransfer.files.length > 0) {
        onFileUpload(e.dataTransfer.files);
      }
    },
    [onFileUpload] // Add onFileUpload to dependencies
  );

  return (
    <div className="flex-1 h-full">
      {selectedBase ? (
        <div className="bg-[#F4F8FB] p-6 shadow-sm h-full  flex flex-col">
          <div className="h-[15%]">
            <div className="flex items-center gap-2 mb-2 justify-between">
              <div className="flex text-[#1570EF] items-center gap-2 max-w-[70%] overflow-scroll scrollbar-hide">
                {/* <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                  className="size-6 mr-2 hover:cursor-pointer text-indigo-500 hover:text-indigo-700"
                  onClick={() => setSelectedBase(null)}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 15 3 9m0 0 6-6M3 9h12a6 6 0 0 1 0 12h-3"
                  />
                </svg> */}

                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="size-6"
                >
                  <path d="M21 6.375c0 2.692-4.03 4.875-9 4.875S3 9.067 3 6.375 7.03 1.5 12 1.5s9 2.183 9 4.875Z" />
                  <path d="M12 12.75c2.685 0 5.19-.586 7.078-1.609a8.283 8.283 0 0 0 1.897-1.384c.016.121.025.244.025.368C21 12.817 16.97 15 12 15s-9-2.183-9-4.875c0-.124.009-.247.025-.368a8.285 8.285 0 0 0 1.897 1.384C6.809 12.164 9.315 12.75 12 12.75Z" />
                  <path d="M12 16.5c2.685 0 5.19-.586 7.078-1.609a8.282 8.282 0 0 0 1.897-1.384c.016.121.025.244.025.368 0 2.692-4.03 4.875-9 4.875s-9-2.183-9-4.875c0-.124.009-.247.025-.368a8.284 8.284 0 0 0 1.897 1.384C6.809 15.914 9.315 16.5 12 16.5Z" />
                  <path d="M12 20.25c2.685 0 5.19-.586 7.078-1.609a8.282 8.282 0 0 0 1.897-1.384c.016.121.025.244.025.368 0 2.692-4.03 4.875-9 4.875s-9-2.183-9-4.875c0-.124.009-.247.025-.368a8.284 8.284 0 0 0 1.897 1.384C6.809 19.664 9.315 20.25 12 20.25Z" />
                </svg>
                <h2 className="text-1xl font-bold">
                  {bases.find((r) => r.baseId === selectedBase)?.name}
                </h2>
              </div>
              <div className="relative w-[25%]">
                <input
                  ref={search1Ref}
                  type="text"
                  placeholder="Search File..."
                  className="w-full pl-6 pr-10 py-1 rounded-full border border-gray-300 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleSearch(search1Ref.current?.value || "");
                      search1Ref.current?.blur();
                    }
                  }}
                />
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="size-6 absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:cursor-pointer"
                  onClick={() => {
                    if (search1Ref.current) {
                      handleSearch(search1Ref.current.value || "");
                      search1Ref.current.blur();
                    }
                  }}
                >
                  <path
                    fillRule="evenodd"
                    d="M10.5 3.75a6.75 6.75 0 1 0 0 13.5 6.75 6.75 0 0 0 0-13.5ZM2.25 10.5a8.25 8.25 0 1 1 14.59 5.28l4.69 4.69a.75.75 0 1 1-1.06 1.06l-4.69-4.69A8.25 8.25 0 0 1 2.25 10.5Z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            </div>

            <div className="flex gap-4 text-sm text-gray-500">
              <span>
                File Number:{" "}
                {bases.find((r) => r.baseId === selectedBase)?.fileNumber}
              </span>
              <span>
                Creat Time:{" "}
                {bases.find((r) => r.baseId === selectedBase)?.createTime}
              </span>
            </div>
          </div>

          {/* 上传区域 */}
          <div
            className={`h-[25%] mb-6 flex flex-col items-center justify-center border-2 border-dashed rounded-2xl p-8 text-center transition-all
                  ${
                    dragActive
                      ? "border-indigo-500 bg-indigo-50 scale-[1.02]"
                      : "border-gray-300"
                  }
                  ${isSendDisabled ? "pointer-events-none opacity-75" : ""}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              className="hidden"
              id="file-upload"
              multiple
              onChange={(e) => e.target.files && onFileUpload(e.target.files)}
              accept=".pdf"
            />
            <label
              htmlFor="file-upload"
              className={`cursor-pointer inline-block px-6 py-2 rounded-full transition-colors
                    ${
                      dragActive
                        ? "bg-indigo-700"
                        : "bg-indigo-500 hover:bg-indigo-700"
                    } text-white`}
            >
              <div className="flex items-center gap-2">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="size-6"
                >
                  <path
                    fillRule="evenodd"
                    d="M19.5 21a3 3 0 0 0 3-3V9a3 3 0 0 0-3-3h-5.379a.75.75 0 0 1-.53-.22L11.47 3.66A2.25 2.25 0 0 0 9.879 3H4.5a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3h15Zm-6.75-10.5a.75.75 0 0 0-1.5 0v2.25H9a.75.75 0 0 0 0 1.5h2.25v2.25a.75.75 0 0 0 1.5 0v-2.25H15a.75.75 0 0 0 0-1.5h-2.25V10.5Z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>{buttonText}</span>
              </div>
            </label>
            <p className="mt-4 text-gray-600">
              Drag files here or click to select
            </p>
            <p className="mt-2 text-sm text-gray-500">Support PDF...</p>
          </div>

          <div className="w-full h-[calc(60%-24px)]">
            <ShowFiles
              files={files}
              onDownload={handleDownload}
              bases={bases}
              pageSize={pageSize}
              setPageSize={setPageSize}
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              totalFiles={totalFiles}
              ondeleteFile={handleDeleteFile}
            />
          </div>
        </div>
      ) : (
        <div className="bg-[#F4F8FB] p-6 h-full flex items-center justify-center shadow-sm flex-col pb-6">
          <div className="flex items-center justify-center h-[10%] w-full">
            <p className="text-gray-500 text-xl">
              Please choose a Knowledge-Base to upload
            </p>
          </div>
          <div className="h-[90%] flex flex-col bg-white rounded-xl shadow-sm p-6 w-[90%]">
            <div className="mb-6 flex items-center justify-between h-[10%]">
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="w-6 h-6"
                >
                  <path d="M19.5 21a3 3 0 003-3v-4.5a3 3 0 00-3-3h-15a3 3 0 00-3 3V18a3 3 0 003 3h15zM1.5 10.146V6a3 3 0 013-3h5.379a2.25 2.25 0 011.59.659l2.122 2.121c.14.141.331.22.53.22H19.5a3 3 0 013 3v1.146A4.483 4.483 0 0019.5 9h-15a4.483 4.483 0 00-3 1.146z" />
                </svg>
                All Files
              </h2>
              <div className="relative w-[25%]">
                <input
                  ref={search2Ref}
                  type="text"
                  placeholder="Search File..."
                  className="w-full pl-6 pr-10 py-1 rounded-full border border-gray-300 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleSearch(search2Ref.current?.value || "");
                      search2Ref.current?.blur();
                    }
                  }}
                />
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="size-6 absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:cursor-pointer"
                >
                  <path
                    fillRule="evenodd"
                    d="M10.5 3.75a6.75 6.75 0 1 0 0 13.5 6.75 6.75 0 0 0 0-13.5ZM2.25 10.5a8.25 8.25 0 1 1 14.59 5.28l4.69 4.69a.75.75 0 1 1-1.06 1.06l-4.69-4.69A8.25 8.25 0 0 1 2.25 10.5Z"
                    clipRule="evenodd"
                    onClick={() => {
                      if (search2Ref.current) {
                        handleSearch(search2Ref.current.value || "");
                        search2Ref.current.blur();
                      }
                    }}
                  />
                </svg>
              </div>
            </div>
            <div className="w-full h-[90%]">
              <ShowFiles
                files={files}
                onDownload={handleDownload}
                bases={bases}
                pageSize={pageSize}
                setPageSize={setPageSize}
                currentPage={currentPage}
                setCurrentPage={setCurrentPage}
                totalFiles={totalFiles}
                ondeleteFile={handleDeleteFile}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBaseDetails;
