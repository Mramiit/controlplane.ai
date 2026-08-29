# File: app/services/rag_pipeline.py
# Problem it solves: Prevents AI hallucinations by giving the model a factual "memory" source. It avoids slow disk reads by keeping the vector database in memory using a Singleton pattern.
# Completed by: Rahul - Implemented the LangChain FAISS vector database using free local HuggingFace embeddings instead of OpenAI.

import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

class RAGPipeline:
    _instance = None

    def __new__(cls):
        # Singleton pattern: Ensures the heavy FAISS index is only loaded into RAM exactly once at startup
        if cls._instance is None:
            cls._instance = super(RAGPipeline, cls).__new__(cls)
            cls._instance.vector_store = None
        return cls._instance

    def initialize_index(self):
        """Loads documents and builds the FAISS index once at startup."""
        if self.vector_store is not None:
            return 
            
        print("Initializing FAISS Index (Downloading local embedding model... this may take a few seconds)...")
        
        # Using the free, fast local model recommended in the architecture documentation
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Pointing to the internal handbook from the data folder as our ground truth
        file_path = "data/scenario_b_internal/employee_handbook.md"
        
        # Fallback safeguard in case the dummy file is empty or missing
        if not os.path.exists(file_path):
            print(f"Warning: Document not found at {file_path}. Creating an empty fallback index.")
            self.vector_store = FAISS.from_texts(["Fallback context: No company documents loaded."], embeddings)
            return

        # Read, split, and embed the document
        loader = TextLoader(file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)
        
        # Build the in-memory vector database
        self.vector_store = FAISS.from_documents(chunks, embeddings)
        print("FAISS Index initialized successfully.")

    async def retrieve_context(self, query: str, top_k: int = 3):
        """Asynchronously retrieves the most relevant document chunks based on the user's question."""
        if self.vector_store is None:
            self.initialize_index()
            
        # Search the database for the top 3 most relevant chunks
        docs = await self.vector_store.asimilarity_search(query, k=top_k)
        return "\n".join([doc.page_content for doc in docs])

# Create a global instance for the orchestration engine to import
rag_pipeline = RAGPipeline()