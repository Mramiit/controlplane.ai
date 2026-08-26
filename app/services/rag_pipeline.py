import os
from typing import Optional
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

class RAGPipeline:
    def __init__(self, embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        # Uses lightweight local embeddings (~80MB) running on CPU
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)
        self.vector_store: Optional[FAISS] = None

    def load_document(self, file_path: str):
        """
        Loads a text/markdown file, chunks it, and builds an in-memory FAISS index.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)
        chunks = splitter.split_text(text)
        
        self.vector_store = FAISS.from_texts(chunks, self.embeddings)

    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """
        Retrieves top-k context chunks relevant to the user query.
        """
        if not self.vector_store:
            return ""
        
        docs = self.vector_store.similarity_search(query, k=top_k)
        return "\n\n".join([doc.page_content for doc in docs])