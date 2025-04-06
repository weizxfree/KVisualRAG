"use client";
import axios, { AxiosProgressEvent } from "axios";
import Cookies from "js-cookie";

const api = axios.create({
  baseURL: `${process.env.NEXT_PUBLIC_API_BASE_URL}`,
});

api.interceptors.request.use((config) => {
  const token = Cookies.get("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle failed token verification globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Redirect to login if token is invalid or expired
      Cookies.remove("token");
      window.location.href = "/sign-in";
    }
    return Promise.reject(error);
  }
);

export const getAllKnowledgeBase = async (username: string) => {
  return api.get("/base/users/" + username + "/knowledge_bases");
};

export const createKnowledgeBase = async (
  username: string,
  knowledgeBaseName: string
) => {
  return api.post("/base/knowledge_base", {
    username: username,
    knowledge_base_name: knowledgeBaseName,
  });
};

export const deleteKnowledgeBase = async (BaseId: string) => {
  return api.delete("/base/knowledge_base/" + BaseId);
};

export const deleteFile = async (BaseId: string, file_id: string) => {
  return api.delete(`/base/file/${BaseId}/${file_id}`);
};

export const renameKnowledgeBase = async (
  baseId: string,
  knowledgeBaseName: string
) => {
  return api.post("/base/knowledge_base/rename", {
    knowledge_base_id: baseId,
    knowledge_base_new_name: knowledgeBaseName,
  });
};

// 获取知识库文件
export const getKBFiles = async (
  kbId: string,
  page: number,
  pageSize: number,
  keyword: string
) => {
  return api.post(`/base/knowledge_bases/${kbId}/files`, {
    keyword: keyword,
    page: page,
    page_size: pageSize,
  });
};

// 获取用户所有文件
export const getUserFiles = async (
  username: string,
  page: number,
  pageSize: number,
  keyword: string
) => {
  return await api.post(`/base/users/${username}/files`, {
    keyword: keyword,
    page: page,
    page_size: pageSize,
  });
};

// 生成下载链接
export const generateDownloadUrl = async (
  username: string,
  minioFilename: string
) => {
  return await axios.post(`/base/files/download`, {
    username: username,
    minio_filename: minioFilename,
  });
};

export const uploadFiles = async (
  selectedFiles: File[],
  knowledgeBaseId: string,
  onProgress: (percent: number | null) => void
) => {
  if (!selectedFiles) return;

  const fileFormData = new FormData();

  selectedFiles.forEach((file) => {
    fileFormData.append("files", file); // 多个文件使用相同字段名
  });

  return api.post("/base/upload/" + knowledgeBaseId, fileFormData, {
    onUploadProgress: (progressEvent: AxiosProgressEvent) => {
      if (progressEvent.lengthComputable && progressEvent.total) {
        const percent = Math.round(
          (progressEvent.loaded / progressEvent.total) * 100
        );
        onProgress(percent); // 调用回调函数并传递进度百分比
      } else {
        // 处理无法计算进度的情况
        onProgress(null); // 或者传递一个特定的值表示进度不可计算
      }
    },
  });
};
