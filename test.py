from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
from colpali_engine.utils.torch_utils import ListDataset, get_torch_device
from torch.utils.data import DataLoader
import torch
from typing import List, cast
from transformers.utils.import_utils import is_flash_attn_2_available
from tqdm import tqdm
from app.core.config import settings
import numpy as np
import os
from peft import PeftModel


base_model_path = "/home/administrator/KnowFlowVisualRAG/colqwen2.5-base"
adapter_path = "/home/administrator/KnowFlowVisualRAG/colqwen2.5-v0.2"

try:
    # 加载基础模型
    model = ColQwen2_5.from_pretrained(base_model_path, local_files_only=True)
    print("Base model loaded successfully")
    # 加载 PEFT 适配器
    model = PeftModel.from_pretrained(model, adapter_path, local_files_only=True)
    print("Adapter loaded successfully")
except Exception as e:
    print(f"Error: {e}")