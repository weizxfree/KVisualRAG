// types.ts
// types.ts
export interface Message {
  type: "text" | "image" | "file" | "thinking" | "baseFile";
  content: string | null;
  thinking?: string;
  fileName?: string; // 新增文件名字段
  fileType?: string; // 新增文件类型字段
  minioUrl?: string;
  messageId?: string;
  baseId?: string;
  score?: number;
  imageMinioUrl?: string;
  token_number?: {
    total_token: number;
    completion_tokens: number;
    prompt_tokens: number;
  };
  from: "user" | "ai"; // 消息的来源
}

export interface Chat {
  name: string;
  conversationId: string;
  lastModityTime: string;
  isRead: boolean;
  createTime: string;
  messages: Message[];
}

export interface Base {
  name: string;
  baseId: string;
  lastModityTime: string;
  createTime: string;
  fileNumber: number;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  selected: boolean;
}

export interface BaseUsed {
  name: string;
  baseId: string;
}

export interface FileRespose {
  id: string;
  minio_filename: string;
  filename: string;
  url: string;
}

// 更新类型定义
export interface ModelConfig {
  modelId: string;
  baseUsed: BaseUsed[];
  modelName: string;
  modelURL: string;
  apiKey: string;
  systemPrompt: string;
  temperature: number;
  maxLength: number;
  topP: number;
  topK: number;
  useTemperatureDefault: boolean;
  useMaxLengthDefault: boolean;
  useTopPDefault: boolean;
  useTopKDefault: boolean;
}

export interface UploadFile {
  id: string;
  name: string;
  progress: number;
  error?: string;
}

export interface KnowledgeFile {
  file_id: string;
  filename: string;
  url: string;
  upload_time: string;
  kb_id: string;
  minio_filename: string;
}

export interface FileUsed {
  knowledge_db_id: string;
  file_name: string;
  image_url: string;
  file_url: string;
  score: number;
}
