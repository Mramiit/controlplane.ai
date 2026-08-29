import os
from typing import Dict
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

class RAGPipeline:
    def __init__(self, embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        # Uses lightweight local embeddings (~80MB) running on CPU
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)
        # One vector store PER SCENARIO, keyed by scenario id, instead of a
        # single shared store. Previously a single `self.vector_store` was
        # reassigned on every load_document() call, so loading the second
        # scenario's document silently wiped out the first scenario's index.
        self.vector_stores: Dict[str, FAISS] = {}

    def load_document(self, file_path: str, scenario: str):
        """
        Loads a text/markdown file, chunks it, and adds it to the FAISS
        index for the given scenario (creating that index if it doesn't
        exist yet, or merging into it if it does).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)
        chunks = splitter.split_text(text)

        if scenario in self.vector_stores:
            self.vector_stores[scenario].add_texts(chunks)
        else:
            self.vector_stores[scenario] = FAISS.from_texts(chunks, self.embeddings)

    def retrieve_context(self, query: str, scenario: str, top_k: int = 3) -> str:
        """
        Retrieves top-k context chunks relevant to the user query, scoped to
        the given scenario's own index only.
        """
        store = self.vector_stores.get(scenario)
        if not store:
            return ""

        docs = store.similarity_search(query, k=top_k)
        return "\n\n".join([doc.page_content for doc in docs])