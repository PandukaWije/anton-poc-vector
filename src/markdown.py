from typing import Optional
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
from dotenv import load_dotenv

load_dotenv()

def html_to_markdown(html_content: str, api_key: Optional[str] = None) -> str:
    """
    Convert HTML content to Markdown format using GPT-4.
    
    Args:
        html_content (str): The HTML content to convert
        api_key (Optional[str]): OpenAI API key. If None, assumes it's set in environment variables
        
    Returns:
        str: The converted Markdown content
    """
    html_content = f"""{html_content}"""
    llm = OpenAI(
                model="gpt-4o",
                temperature=0.0,
                api_key=api_key
                )

    messages = [
                ChatMessage(
                            role="system", 
                            content="You are a helpful assistant that converts HTML to Markdown. "
                                    "Provide only the converted Markdown without any explanations."
                ),
                ChatMessage(role="user", content=f"Convert this HTML to Markdown:\n\n{html_content}")
                ]
    
    response = llm.chat(messages)
    content = response.message.content.strip()
    return content