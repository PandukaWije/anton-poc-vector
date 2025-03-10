import os, pickle, json
from dotenv import load_dotenv
from llama_index.core import Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import VectorStoreIndex, Settings, SimpleDirectoryReader
from dotenv import load_dotenv
from src.scraper import *

load_dotenv()

class RAGChat:
    def __init__(
                self, 
                documents_path: str,
                website_url = "https://onlinestore.anton.lk",
                support_email = "support@onlinestore.anton.lk",
                business_name = "Anton"
                ):
        """
        Initialize RAG chat with documents from the specified path
        """
        self.system_prompt = f"""
        
        You are a helpful travel assistant for {website_url}. Use the provided context to answer 
        the user's questions accurately and professionally. 

        -------------------------------------------------------------------------------------------------------------

        For greetings and basic interactions (like "hi", "hello", "how are you", etc.), respond naturally and warmly.
        
        -------------------------------------------------------------------------------------------------------------
        If the questions related to
                - Pressure Pipes & Fittings
                - Non Pressure Pipes & Fittings
                - Thermo CPVC Pipes & Fittings
                - Adhesives & Sealants
                - Valves
                - Volta Conduits & Trunking
                - Water Tanks
                - NetZ
                - Hoses
                - Polar Insulation

        Answer the questions based on the website content.
        -------------------------------------------------------------------------------------------------------------   
        
        For all other questions, 
        
        1. if you don't find relevant information in the provided context to answer accurately but still relevant to the {website_url} website, 
        respond with:
        
        "Kindly note that our operations team has limited availability after 6:00 PM PST. Therefore, messages received after this time may not be addressed until the following morning. We appreciate your understanding and patience."
        
        2. if you don't find relevant information in the provided context to answer accurately and not related to the {website_url} website, 
        respond with:

        "I apologize, but I can only assist with questions related to {business_name}'s services. For other topics, please visit {website_url} or contact our support team at {support_email} for personalized assistance. We're here to help you with all your business inquiries!"
        
        -------------------------------------------------------------------------------------------------------------
        """
        
        # Initialize OpenAI with GPT-4 and embedding models
        self.llm = OpenAI(
                        model="o3-mini-2025-01-31",
                        temperature=0.3,
                        api_key=os.environ["OPENAI_API_KEY"],
                        system_prompt=self.system_prompt
                        )
        self.embed_model = OpenAIEmbedding(
                                        model="text-embedding-3-small",
                                        api_key=os.environ["OPENAI_API_KEY"]
                                        )
        
        # Create query engine with response synthesis
        self.website_url = website_url
        self.scrape()

        self.enc = tiktoken.encoding_for_model("gpt-4o")
        self.splitter = SentenceSplitter(
                                        chunk_size=Settings.chunk_size, 
                                        chunk_overlap=Settings.chunk_overlap
                                        )
        self.scraped_json = "processed/scraped.json"
        self.index_path = "processed/index.pkl"

        # Configure global settings
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        Settings.chunk_overlap = 512
        Settings.chunk_size = 4096

    def create_index(self):
        if os.path.exists(self.index_path):
            with open(self.index_path, 'rb') as f:
                self.index = pickle.load(f)
        else:
            self.documents = self.preprocess_data()
            self.index = VectorStoreIndex.from_documents(self.documents)
            with open(self.index_path, 'wb') as f:
                pickle.dump(self.index, f)
                
        self.query_engine = self.index.as_query_engine(
                                                    response_mode="compact",
                                                    system_prompt=self.system_prompt,
                                                    streaming=True
                                                    )
    def preprocess_data(self):
        json_data = json.load(open(self.scraped_json))

        documents = []
        for item in json_data:
            content = item['content']
            
            if len(enc.encode(content)) > Settings.chunk_size:
                chunks = self.splitter.split_text(content)
                
                # Create document for each chunk
                for i, chunk in enumerate(chunks):
                    chunk_doc = Document(
                        text=chunk,
                        metadata={
                            **item['metadata'],
                            'chunk_id': i
                        }
                    )
                    documents.append(chunk_doc)
            else:
                doc = Document(
                    text=content,
                    metadata=item['metadata']
                )
                documents.append(doc)
        return documents

    def scrape(
                self,
                scraped_json = "processed/scraped.json"
                ) -> dict:
        if not os.path.exists(scraped_json):
            extracted_data = fetch_and_extract_url_data(self.website_url)
            save_extracted_data(extracted_data, scraped_json)

    def chat(self, query: str) -> str:
        """
        Query the RAG system with a question
        """
        response = str(self.query_engine.query(query))
        return response
