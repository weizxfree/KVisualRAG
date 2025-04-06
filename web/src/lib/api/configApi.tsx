"use client";
import { ModelConfig } from "@/types/types";
import axios from "axios";
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

export const getAllModelConfig = async (username: string) => {
  return api.get("/config/" + username + "/all");
};

export const updateModelConfig = async (
  username: string,
  modelConfig: ModelConfig
) => {
  return api.patch(`/config/${username}/${modelConfig.modelId}`, {
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
  });
};

export const addModelConfig = async (
  username: string,
  modelConfig: ModelConfig
) => {
  return api.post("/config/" + username, {
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
  });
};

export const deleteModelConfig = async (username: string, modelId: string) => {
  return api.delete(`/config/${username}/${modelId}`);
};
