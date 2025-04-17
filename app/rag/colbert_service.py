# app/core/colbert_service.py
from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
from colpali_engine.utils.torch_utils import ListDataset, get_torch_device
from torch.utils.data import DataLoader
import torch
from typing import List, cast
from transformers.utils.import_utils import is_flash_attn_2_available
from tqdm import tqdm
from app.core.config import settings
import numpy as np


class ColBERTService:
    def __init__(self, model_path):
        self.device = torch.device(get_torch_device("auto"))
        self.model = ColQwen2_5.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map=self.device,
            attn_implementation=(
                "flash_attention_2" if is_flash_attn_2_available() else None
            ),
        ).eval()
        self.processor = cast(
            ColQwen2_5_Processor,
            ColQwen2_5_Processor.from_pretrained(
                model_path, size={"shortest_edge": 56 * 56, "longest_edge": 28 * 28 * 768}
            ),
        )

    def process_query(self, queries: list) -> List[torch.Tensor]:
        dataloader = DataLoader(
            dataset=ListDataset[str](queries),
            batch_size=1,
            shuffle=False,
            collate_fn=lambda x: self.processor.process_queries(x),
        )

        qs: List[torch.Tensor] = []
        for batch_query in dataloader:
            with torch.no_grad():
                batch_query = {
                    k: v.to(self.model.device) for k, v in batch_query.items()
                }
                embeddings_query = self.model(**batch_query)
            qs.extend(list(torch.unbind(embeddings_query.to("cpu"))))
        for i in range(len(qs)):
            qs[i] = qs[i].float().tolist()
        return qs

    def process_image(self, images: List) -> List[List[float]]:
        batch_size = 1 # if len(images) > 2 else len(images)
        dataloader = DataLoader(
            dataset=ListDataset[str](images),
            batch_size=batch_size,
            shuffle=False,
            collate_fn=lambda x: self.processor.process_images(x),
        )

        ds: List[torch.Tensor] = []
        for batch_doc in tqdm(dataloader):
            with torch.no_grad():
                batch_doc = {k: v.to(self.model.device) for k, v in batch_doc.items()}
                embeddings_doc = self.model(**batch_doc)
            ds.extend(list(torch.unbind(embeddings_doc.to("cpu"))))
        for i in range(len(ds)):
            ds[i] = ds[i].float().tolist()
        return ds


colbert = ColBERTService(settings.colbert_model_path)
