"use client";
import { BaseUsed, ModelConfig } from "@/types/types";
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

export const login = async (name: string, password: string) => {
  const formData = new FormData();
  formData.append("username", name);
  formData.append("password", password);

  return api.post(
    "/auth/login",
    formData, // This is form data
    { headers: { "Content-Type": "multipart/form-data" } } // This is optional; axios sets it automatically
  );
};

export const verifyToken = async () => {
  return api.get("/auth/verify-token");
};

export const refreshToken = async () => {
  return api.post("/auth/refresh-token");
};

export const register = async (
  name: string,
  email: string,
  password: string
) => {
  return api.post("/auth/register", { username: name, email, password });
};

export const getChatHistory = async (username: string) => {
  return api.get("/chat/users/" + username + "/conversations");
};

export const renameChat = async (conversationId: string, chatName: string) => {
  return api.post("/chat/conversations/rename", {
    conversation_id: conversationId,
    conversation_new_name: chatName,
  });
};

export const getChatContent = async (conversationId: string) => {
  return api.get("/chat/conversations/" + conversationId);
};

export const deleteConversations = async (conversationId: string) => {
  return api.delete("/chat/conversations/" + conversationId);
};

export const deleteAllConversations = async (username: string) => {
  return api.delete("/chat/users/" + username + "/conversations");
};

export const uploadFiles = async (
  selectedFiles: File[],
  username: string,
  chatId: string,
  onProgress: (percent: number | null) => void
) => {
  if (!selectedFiles) return;

  const fileFormData = new FormData();

  selectedFiles.forEach((file) => {
    fileFormData.append("files", file); // 多个文件使用相同字段名
  });

  return api.post("/chat/upload/" + username + "/" + chatId, fileFormData, {
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

export const createConversation = async (
  conversationId: string,
  username: string,
  conversationName: string,
  modelConfig: ModelConfig
) => {
  const sendModelConfig = {
    model_name: modelConfig.modelName,
    model_url: modelConfig.modelURL,
    api_key: modelConfig.apiKey,
    base_used: modelConfig.baseUsed,
    system_prompt: modelConfig.systemPrompt,
    temperature: modelConfig.useTemperatureDefault
      ? -1
      : modelConfig.temperature,
    max_length: modelConfig.useMaxLengthDefault ? -1 : modelConfig.maxLength,
    top_P: modelConfig.useTopPDefault ? -1 : modelConfig.topP,
    top_K: modelConfig.useTopKDefault ? -1 : modelConfig.topK,
  };

  return api.post("/chat/conversations", {
    conversation_id: conversationId,
    username: username,
    conversation_name: conversationName,
    chat_model_config: sendModelConfig,
  });
};

export const updateChatModelConfig = async (
  conversationId: string,
  modelConfig: ModelConfig
) => {
  const sendModelConfig = {
    model_name: modelConfig.modelName,
    model_url: modelConfig.modelURL,
    api_key: modelConfig.apiKey,
    base_used: modelConfig.baseUsed,
    system_prompt: modelConfig.systemPrompt,
    temperature: modelConfig.useTemperatureDefault
      ? -1
      : modelConfig.temperature,
    max_length: modelConfig.useMaxLengthDefault ? -1 : modelConfig.maxLength,
    top_P: modelConfig.useTopPDefault ? -1 : modelConfig.topP,
    top_K: modelConfig.useTopKDefault ? -1 : modelConfig.topK,
  };

  return api.post("/chat/conversations/config", {
    conversation_id: conversationId,
    chat_model_config: sendModelConfig,
  });
};
