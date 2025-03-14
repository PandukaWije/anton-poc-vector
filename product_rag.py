import os
import re
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import AsyncGenerator

# Load environment variables from .env file
load_dotenv()

# Create async OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ProductRAG:
    def __init__(self, markdown_file_path=None, markdown_content=None):
        """
        Initialize the RAG system with product data.
        Either provide a file path or markdown content directly.
        """
        self.markdown_file_path = markdown_file_path
        if markdown_content:
            self.product_data = markdown_content
        elif markdown_file_path:
            self.product_data = self._load_markdown_file()
        else:
            self.product_data = ""
    
    def _load_markdown_file(self):
        """Load and read the markdown file."""
        try:
            with open(self.markdown_file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error loading markdown file: {e}")
            return ""
    
    def get_system_prompt(self, user_question=None):
        """Generate the system prompt with product data and instructions."""
        if not self.product_data:
            return "Error: No product data available."
        
        return f"""
        You are a product information assistant. Below is the product catalog information:
        
        {self.product_data}
        
        Instructions for answering:
        1. Answer questions only based on the product information provided above.
        2. If asked about a specific product, provide all available details for that product.
        3. For every query, be explicit about in-stock status and the website link (URL).
        4. When mentioning prices, always include the currency symbol.
        5. If information is not available in the provided data, politely state that you don't have that information.
        6. Keep responses concise and focused on the question asked.
        7. Format the response in a clear, readable way.
        8. Do not make up or assume any product information not present in the data.
        9. Use markdown formatting when appropriate to make your response more readable.
        """
    
    async def query(self, user_question):
        """
        Query the product information based on user question.
        Uses OpenAI API to generate a response based on the product data.
        """
        if not self.product_data:
            return "Error: No product data available. Please check the markdown file."
        
        system_prompt = self.get_system_prompt()
        
        try:
            # Call OpenAI API
            response = await client.chat.completions.create(
                model="gpt-4o",  
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                temperature=0.1  # Lower temperature for more factual responses
            )
            
            # Return the assistant's response
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error querying OpenAI API: {e}")
            return f"Error processing your request: {str(e)}"
    
    async def stream_query(self, user_question) -> AsyncGenerator[str, None]:
        """
        Stream the response from OpenAI API for a given user question.
        """
        if not self.product_data:
            yield "Error: No product data available. Please check the markdown file."
            return
        
        system_prompt = self.get_system_prompt()
        
        try:
            # Call OpenAI API with streaming
            stream = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                temperature=0.1,
                stream=True
            )
            
            # Yield each chunk as it arrives
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            print(f"Error streaming from OpenAI API: {e}")
            yield f"Error processing your request: {str(e)}"

# Example usage with async
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Initialize the RAG system with your markdown file
        rag = ProductRAG("product_catalog.md")
        
        # Interactive query loop
        print("Product Information Assistant (type 'exit' to quit)")
        print("-------------------------------------------------")
        
        while True:
            user_input = input("\nAsk a question about our products: ")
            
            if user_input.lower() in ['exit', 'quit']:
                print("Thank you for using the Product Information Assistant!")
                break
            
            print("\nStreaming response:")
            async for text_chunk in rag.stream_query(user_input):
                print(text_chunk, end="", flush=True)
            print("\n")
    
    # Run the async main function
    asyncio.run(main())