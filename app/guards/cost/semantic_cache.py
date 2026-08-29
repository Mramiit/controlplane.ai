from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

class SemanticCache:
    def __init__(self, distance_threshold: float = 0.5): 
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.threshold = distance_threshold
        
        dummy_doc = Document(
            page_content="ControlPlane System Initialization", 
            metadata={"response": "initialized", "scenario": "none"}
        )
        self.vector_store = FAISS.from_documents([dummy_doc], self.embeddings)

    def check_cache(self, query: str, scenario: str):
        """Searches vectors but strictly filters by scenario metadata."""
        results = self.vector_store.similarity_search_with_score(query, k=1)
        
        if results:
            doc, score = results[0]
            # The hard logical check preventing semantic bleed
            if score < self.threshold and doc.metadata.get("scenario") == scenario:
                return doc.metadata.get("response")
        return None

    def add_to_cache(self, query: str, response: str, scenario: str):
        """Embeds the query and securely tags the policy scenario."""
        new_doc = Document(
            page_content=query, 
            metadata={"response": response, "scenario": scenario}
        )
        self.vector_store.add_documents([new_doc])