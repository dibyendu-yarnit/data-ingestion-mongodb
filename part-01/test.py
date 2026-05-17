from vectorstore import MongoDBVectorStore
from processings import text_splitter
from openai_ import openai_handler
from loader import pdf_loader

# # Step 01: Load the Pdf:
# pdf_path = "./sample.pdf"
# pdf_text = pdf_loader.extract_text_from_pdf(pdf_path)

# # print("Extracted Text:")
# # print(pdf_text)


# # Step 02: Split the text into chunks:
# chunks = text_splitter.split_documents(documents=[{"content": pdf_text, "metadata": {"source": pdf_path}}], extra_metadata={"source": pdf_path, "type": "pdf", "filename": pdf_path.split("/")[-1]})

# # print("\nText Chunks:")
# # print(chunks[0])
# # print(len(chunks))


# Step 03: Create the Vector Store and add chunks:
vector_store = MongoDBVectorStore(
    collection_name="pdf_chunks",
    generate_embedding=openai_handler.get_embedding,
    embedding_dimensions=1536,
    vector_index_name = "vector_index",
    search_index_name = "search_index",
)


# # One-time setup — run once per collection, then comment out
# vector_store.create_vector_index(similarity="cosine") 
# vector_store.create_search_index()


# # Step 04: Add chunks to the vector store:
# inserted_ids = vector_store.add_chunks(chunks=chunks)
# print("\nInserted Document IDs: ")
# print(inserted_ids)


# # Step 05: Perform a similarity search with metadata filtering:
# query = "What is the main topic of the document?"
# similar_chunks = vector_store.similarity_search(query=query, k=3, filter={"metadata.source": "sample.pdf"})
# print("\nSimilar Chunks:")
# for idx, chunk in enumerate(similar_chunks):
#     print(f"\nChunk {idx+1}:")
#     print(f"Content: {chunk['content']}")
#     print(f"Metadata: {chunk['metadata']}")
