from pymilvus import MilvusClient, DataType
import numpy as np
import concurrent.futures
from app.core.config import settings


class MilvusManager:
    def __init__(self):
        self.client = MilvusClient(uri=settings.milvus_uri)

    def delete_collection(self, collection_name: str):
        if self.client.has_collection(collection_name):
            self.client.drop_collection(collection_name)
            return True
        else:
            return False

    def delete_files(self, collection_name: str, file_ids: list):
        filter = "file_id in ["
        for file_id in file_ids:
            filter += f"'{file_id}', "
        filter += "]"
        res = self.client.delete(
            collection_name=collection_name,
            filter=filter,
        )
        return res

    def check_collection(self, collection_name: str):
        if self.client.has_collection(collection_name):
            return True
        else:
            return False

    def create_collection(self, collection_name: str, dim: int = 128) -> None:

        if self.client.has_collection(collection_name):
            self.client.drop_collection(collection_name)

        schema = self.client.create_schema(
            auto_id=True,
            enable_dynamic_fields=True,
        )
        schema.add_field(field_name="pk", datatype=DataType.INT64, is_primary=True)
        schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=dim)
        schema.add_field(
            field_name="image_id", datatype=DataType.VARCHAR, max_length=65535
        )
        schema.add_field(field_name="page_number", datatype=DataType.INT64)
        schema.add_field(
            field_name="file_id", datatype=DataType.VARCHAR, max_length=65535
        )

        self.client.create_collection(collection_name=collection_name, schema=schema)
        self._create_index(collection_name)

    def _create_index(self, collection_name):
        # Create an index on the vector field to enable fast similarity search.
        # Releases and drops any existing index before creating a new one with specified parameters.
        self.client.release_collection(collection_name=collection_name)
        self.client.drop_index(collection_name=collection_name, index_name="vector")
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_name="vector_index",
            index_type="HNSW",  # or any other index type you want
            metric_type="IP",  # or the appropriate metric type
            params={
                "M": 16,
                "efConstruction": 500,
            },  # adjust these parameters as needed
        )

        self.client.create_index(
            collection_name=collection_name, index_params=index_params, sync=True
        )
        self.client.load_collection(collection_name)

    def search(self, collection_name, data, topk):
        # Perform a vector search on the collection to find the top-k most similar documents.
        search_params = {"metric_type": "IP", "params": {}}
        results = self.client.search(
            collection_name,
            data,
            limit=int(50),
            output_fields=["vector", "image_id", "page_number", "file_id"],
            search_params=search_params,
        )
        image_ids = set()
        for r_id in range(len(results)):
            for r in range(len(results[r_id])):
                image_ids.add(results[r_id][r]["entity"]["image_id"])

        scores = []

        def rerank_single_doc(image_id, data, client, collection_name):
            # Rerank a single document by retrieving its embeddings and calculating the similarity with the query.
            doc_colbert_vecs = client.query(
                collection_name=collection_name,
                filter=f"image_id in ['{image_id}']",
                output_fields=["vector", "image_id", "page_number", "file_id"],
                limit=1000,
            )
            # 提取元数据（假设同一 image_id 对应的 file_id 和 page_number 是相同的）
            if not doc_colbert_vecs:
                return (
                    0.0,
                    {"image_id": image_id, "file_id": None, "page_number": None},
                )

            # 取第一条记录的元数据（假设同一 image_id 的 file_id 和 page_number 一致）
            metadata = {
                "image_id": image_id,
                "file_id": doc_colbert_vecs[0]["file_id"],
                "page_number": doc_colbert_vecs[0]["page_number"],
            }

            doc_vecs = np.vstack(
                [doc_colbert_vecs[i]["vector"] for i in range(len(doc_colbert_vecs))]
            )
            score = np.dot(data, doc_vecs.T).max(1).sum()
            return (score, metadata)

        with concurrent.futures.ThreadPoolExecutor(max_workers=300) as executor:
            futures = {
                executor.submit(
                    rerank_single_doc, image_id, data, self.client, collection_name
                ): image_id
                for image_id in image_ids
            }
            for future in concurrent.futures.as_completed(futures):
                score, metadata = future.result()
                scores.append((score, metadata))  # 保存元数据

        scores.sort(key=lambda x: x[0], reverse=True)
        # 返回 Top-K 结果，包含所有字段
        return [
            {
                "score": score,
                "image_id": metadata["image_id"],
                "file_id": metadata["file_id"],
                "page_number": metadata["page_number"],
            }
            for score, metadata in scores[:topk]
        ]

    def insert(self, data, collection_name):
        # Insert ColQwen embeddings and metadata for a document into the collection.
        colqwen_vecs = [vec for vec in data["colqwen_vecs"]]
        seq_length = len(colqwen_vecs)

        # Insert the data as multiple vectors (one for each sequence) along with the corresponding metadata.
        self.client.insert(
            collection_name,
            [
                {
                    "vector": colqwen_vecs[i],
                    "image_id": data["image_id"],
                    "page_number": data["page_number"],
                    "file_id": data["file_id"],
                }
                for i in range(seq_length)
            ],
        )


milvus_client = MilvusManager()
