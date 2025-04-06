import { Base, KnowledgeFile } from "@/types/types";
import { Dispatch, SetStateAction, useState } from "react";
import ConfirmDialog from "../ConfirmDialog";

interface ShowFilesProps {
  files: KnowledgeFile[];
  onDownload: (file: KnowledgeFile) => Promise<void>;
  bases: Base[];
  pageSize: number;
  setPageSize: Dispatch<SetStateAction<number>>;
  currentPage: number;
  setCurrentPage: Dispatch<SetStateAction<number>>;
  totalFiles: number;
  ondeleteFile: (file: KnowledgeFile) => void;
}

const ShowFiles: React.FC<ShowFilesProps> = ({
  files,
  onDownload,
  bases,
  pageSize,
  setPageSize,
  currentPage,
  setCurrentPage,
  totalFiles,
  ondeleteFile,
}) => {
  const [showConfirmDeleteFile, setShowConfirmDeleteFile] = useState<{
    index: number;
    file: KnowledgeFile;
  } | null>(null);

  const handleDeleteFile = (file: KnowledgeFile, index: number) => {
    setShowConfirmDeleteFile({ index, file }); // 显示单个对话框
  };

  const confirmDeleteFile = () => {
    if (showConfirmDeleteFile) {
      ondeleteFile(showConfirmDeleteFile.file);
      setShowConfirmDeleteFile(null); // 关闭对话框
    }
  };

  const cancelDeleteFile = () => {
    if (showConfirmDeleteFile) {
      setShowConfirmDeleteFile(null); // 关闭对话框
    }
  };

  return (
    <div className="flex flex-col w-full h-full">
      {/* 文件列表 */}
      <div className="flex-1 overflow-auto mb-4">
        {files.map((file, index) => (
          <div
            key={index}
            className="flex items-center justify-between p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-200"
          >
            <div
              className="flex items-center justify-between w-[calc(100%-24px)]"
              onClick={() => onDownload(file)}
            >
              <div className="flex-1">
                <div className="font-medium text-sm">{file.filename}</div>
                <div className="text-sm text-gray-500">
                  {new Date(file.upload_time).toLocaleDateString()}
                  {file.kb_id &&
                    ` · Knowledge-Base: ${
                      bases.find((b) => b.baseId === file.kb_id)?.name
                    }`}
                </div>
              </div>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="w-5 h-5 text-indigo-500 hover:text-indigo-700"
              >
                <path
                  fillRule="evenodd"
                  d="M12 2.25a.75.75 0 01.75.75v11.69l3.22-3.22a.75.75 0 111.06 1.06l-4.5 4.5a.75.75 0 01-1.06 0l-4.5-4.5a.75.75 0 111.06-1.06l3.22 3.22V3a.75.75 0 01.75-.75zm-9 13.5a.75.75 0 01.75.75v2.25a1.5 1.5 0 001.5 1.5h13.5a1.5 1.5 0 001.5-1.5V16.5a.75.75 0 011.5 0v2.25a3 3 0 01-3 3H5.25a3 3 0 01-3-3V16.5a.75.75 0 01.75-.75z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="1.5"
              stroke="currentColor"
              className="size-5 text-indigo-500 hover:text-indigo-700"
              onClick={() => handleDeleteFile(file, index)}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
              />
            </svg>
          </div>
        ))}
        {files.length === 0 && (
          <div className="text-center text-gray-500 py-8">No Files</div>
        )}
      </div>
      {/* 分页控件 */}
      <div className="flex justify-between items-center mt-auto">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Display Per Page</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="cursor-pointer border border-gray-200 px-2 py-1 text-sm rounded-xl appearance-none text-gray-700 bg-white focus:outline-hidden"
          >
            {[5, 10, 20, 50].map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="cursor-pointer disabled:cursor-not-allowed px-3 py-1 border border-gray-200 disabled:opacity-50 bg-indigo-500 text-white hover:bg-indigo-700 rounded-full"
          >
            Previous
          </button>
          <span className="text-sm">
            Page {currentPage} of {Math.ceil(totalFiles / pageSize)}
          </span>
          <button
            onClick={() => setCurrentPage(currentPage + 1)}
            disabled={currentPage >= Math.ceil(totalFiles / pageSize)}
            className="cursor-pointer disabled:cursor-not-allowed px-6 py-1 border border-gray-200 disabled:opacity-50 bg-indigo-500 text-white hover:bg-indigo-700 rounded-full"
          >
            Next
          </button>
        </div>
      </div>
      {/* 确认删除单个文件 */}
      {showConfirmDeleteFile && (
        <ConfirmDialog
          message={`Confirm the deletion of file "${showConfirmDeleteFile.file.filename.slice(
            0,
            30
          )}"？`}
          onConfirm={confirmDeleteFile}
          onCancel={cancelDeleteFile}
        />
      )}
    </div>
  );
};

export default ShowFiles;
