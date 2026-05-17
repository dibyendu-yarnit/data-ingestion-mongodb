from pymongo.operations import SearchIndexModel
from pymongo.errors import CollectionInvalid
from pymongo import MongoClient
from dotenv import load_dotenv
import time
import os


# Load environment variables from .env file
load_dotenv()

# Load the Secret Key from environment variable
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "vectorstore_db")



class MongoDBVectorStore:
    def __init__(
        self,
        collection_name: str,
        generate_embedding: callable,
        embedding_model: str = "text-embedding-3-small",
        embedding_dimensions: int = 1536,
        mongo_uri: str=MONGO_URI,
        mongo_db: str=MONGO_DB,
        vector_index_name: str = "vector_index",
        search_index_name: str = "search_index",
    ):
        try:
            self.client = MongoClient(mongo_uri)
            self.db = self.client[mongo_db]

            try:
                self.db.create_collection(collection_name)
            except CollectionInvalid:
                pass 

            self.collection = self.db[collection_name]
            self.embedding_model = embedding_model
            self.generate_embedding = generate_embedding
            self.embedding_dimensions = embedding_dimensions
            self.vector_index_name = vector_index_name
            self.search_index_name = search_index_name

        except Exception as exc:
            raise RuntimeError(f"Failed to initialize VectorStore: {exc}") from exc

    
    def create_vector_index(
        self,
        similarity: str = "cosine",
        extra_filter_fields: list[str] | None = None,
    ) -> None:
        """
            Create an Atlas Vector Search index (type='vectorSearch') on 'embedding'.

            similarity: "cosine" | "euclidean" | "dotProduct"
            extra_filter_fields: additional metadata dot-paths to register as
                                filter fields beyond the defaults.
            Requires Atlas M10+. Builds asynchronously — wait for READY status.
        """
        try:
            base_filters = [
                "metadata.source",
                "metadata.ingested_at",
                "metadata.name",
                "metadata.type",
                "chunk_index",
            ]
            all_filters = base_filters + (extra_filter_fields or [])

            fields = [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": self.embedding_dimensions,
                    "similarity": similarity,
                }
            ] + [{"type": "filter", "path": p} for p in all_filters]

            index_model = SearchIndexModel(
                definition={"fields": fields},
                name=self.vector_index_name,
                type="vectorSearch",
            )

            self.collection.create_search_indexes([index_model])
            print(f"Vector search index '{self.vector_index_name}' creation initiated.")
            print(f"Filter fields indexed: {all_filters}")

        except Exception as exc:
            raise RuntimeError(f"Failed to create vector index: {exc}") from exc


    def create_search_index(self) -> None:
        """
            Create an Atlas Search index (type='search') on the 'content' field.

            This is a full Atlas Search index — NOT a basic MongoDB $text index.
            It powers the $search stage inside hybrid_search().
            Requires Atlas M10+. Builds asynchronously — wait for READY status.
        """
        try:
            index_model = SearchIndexModel(
                definition={
                    "mappings": {
                        "dynamic": False,
                        "fields": {
                            "content": [{"type": "string"}],
                        },
                    }
                },
                name=self.search_index_name,
                type="search",
            )
            self.collection.create_search_indexes([index_model])
            print(f"Atlas Search index '{self.search_index_name}' creation initiated.")

        except Exception as exc:
            raise RuntimeError(f"Failed to create search index: {exc}") from exc

    
    def update_vector_index(
        self,
        similarity: str = "cosine",
        filter_fields: list[str] | None = None,
    ) -> None:
        """
            Update the existing vector index with a new filter field list.
            Replaces the entire filter definition — include all fields you need.
            Atlas rebuilds asynchronously — wait for READY before querying.
        """
        try:
            filter_paths = filter_fields or [
                "metadata.source",
                "metadata.ingested_at",
                "metadata.name",
                "metadata.type",
                "chunk_index",
            ]
            fields = [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": self.embedding_dimensions,
                    "similarity": similarity,
                }
            ] + [{"type": "filter", "path": p} for p in filter_paths]

            self.collection.update_search_index(
                name=self.vector_index_name,
                definition={"fields": fields},
            )
            print(f"Vector index '{self.vector_index_name}' update initiated.")
            print(f"New filter fields: {filter_paths}")

        except Exception as exc:
            raise RuntimeError(f"Failed to update vector index: {exc}") from exc

    
    def add_chunks(self, chunks: list[dict]) -> list:
        """
            Embed each chunk's 'content', attach the vector as 'embedding',
            stamp 'metadata.ingested_at', and bulk-insert into MongoDB.

            Expected chunk shape (from RecursiveCharacterSplitter.split_documents):
                {"content": str, "chunk_index": int, "token_count": int, "metadata": dict}
        """
        try:
            if not chunks:
                return []

            timestamp = time.time()
            docs = []
            for chunk in chunks:
                embedding = self.generate_embedding(chunk["content"])
                doc = {**chunk, "embedding": embedding}
                doc["metadata"]["ingested_at"] = timestamp
                docs.append(doc)

            result = self.collection.insert_many(docs)
            return result.inserted_ids

        except Exception as exc:
            raise RuntimeError(f"Failed to add chunks: {exc}") from exc

    

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        num_candidates: int = 100,
        filter: dict | None = None,
        min_score: float = 0.0,
    ) -> list[dict]:
        """
            Pure vector similarity search via Atlas $vectorSearch (ANN).
            Each result includes a 'score' field (0-1, higher = more similar).

            filter: MQL pre-filter on indexed fields, e.g. {"metadata.name": "arko"}
            min_score: drop results below this threshold.
        """
        try:
            query_embedding = self.generate_embedding(query)

            vector_search: dict = {
                "index": self.vector_index_name,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": max(num_candidates, k * 10),
                "limit": k,
            }
            if filter:
                vector_search["filter"] = filter

            pipeline = [
                {"$vectorSearch": vector_search},
                {
                    "$project": {
                        "embedding": 0,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
            ]
            if min_score > 0.0:
                pipeline.append({"$match": {"score": {"$gte": min_score}}})

            return list(self.collection.aggregate(pipeline))

        except Exception as exc:
            raise RuntimeError(f"Similarity search failed: {exc}") from exc

    def hybrid_search(
        self,
        query: str,
        k: int = 5,
        num_candidates: int = 100,
        vector_weight: float = 0.7,
        fulltext_weight: float = 0.3,
        filter: dict | None = None,
    ) -> list[dict]:
        """
            Hybrid search using MongoDB's native $rankFusion pipeline stage.

            Runs two sub-pipelines inside a single aggregation and fuses their
            ranked results using Reciprocal Rank Fusion with configurable weights:

            vector   sub-pipeline: $vectorSearch on 'embedding'
            fulltext sub-pipeline: $search (Atlas Search) on 'content'

            Requires both indexes to be in READY state:
            - vector_index  → created with create_vector_index()
            - search_index  → created with create_search_index()   ← Atlas Search

            filter: MQL filter applied to $vectorSearch pre-filter AND as a
                    post-$rankFusion $match, so both sub-pipelines' results
                    are correctly scoped.

            Note: $rankFusion is an Atlas preview feature (Atlas M10+ required).
        """
        try:
            query_embedding = self.generate_embedding(query)

            vector_stage: dict = {
                "index": self.vector_index_name,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": max(num_candidates, k * 10),
                "limit": k,
            }
            if filter:
                vector_stage["filter"] = filter

            pipeline = [
                {
                    "$rankFusion": {
                        "input": {
                            "pipelines": {
                                "vector": [
                                    {"$vectorSearch": vector_stage}
                                ],
                                "fulltext": [
                                    {
                                        "$search": {
                                            "index": self.search_index_name,
                                            "text": {
                                                "query": query,
                                                "path": "content",
                                            },
                                        }
                                    },
                                    {"$limit": k},
                                ],
                            }
                        },
                        "combination": {
                            "weights": {
                                "vector": vector_weight,
                                "fulltext": fulltext_weight,
                            }
                        },
                    }
                },
                # Post-fusion filter — enforces filter on fulltext results too,
                # since $search inside $rankFusion cannot accept a pre-filter.
                *([ {"$match": filter} ] if filter else []),
                {"$limit": k},
                {"$project": {"embedding": 0}},
            ]

            return list(self.collection.aggregate(pipeline))

        except Exception as exc:
            raise RuntimeError(f"Hybrid search failed: {exc}") from exc
