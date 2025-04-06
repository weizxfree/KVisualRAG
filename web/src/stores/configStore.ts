import { ModelConfig } from "@/types/types";
import { create } from "zustand";

interface ModelConfigStore {
  modelConfig: ModelConfig;
  setModelConfig: (
    updater: ModelConfig | ((prev: ModelConfig) => ModelConfig)
  ) => void;
}

const useModelConfigStore = create<ModelConfigStore>((set) => ({
  modelConfig: {
    baseUsed: [],
    modelId: "",
    modelName: "qwen2.5-vl-32b-instruct",
    modelURL: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    apiKey: "sk-default-xxx",
    systemPrompt: "All outputs in Markdown format, especially mathematical formulas in Latex format($formula$).",
    temperature: 0.1,
    maxLength: 8096,
    topP: 0.01,
    topK: 3,
    useTemperatureDefault: true,
    useMaxLengthDefault: true,
    useTopPDefault: true,
    useTopKDefault: true,
  },
  setModelConfig: (updater) => 
    set((state) => ({
      modelConfig: typeof updater === "function" 
        ? updater(state.modelConfig)
        : updater
    })),
}));

export default useModelConfigStore;
