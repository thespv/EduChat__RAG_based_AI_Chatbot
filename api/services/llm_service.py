import os
import re
import json
from typing import List, Dict, Any
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

for key in ["GEMINI_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY"]:
    if not os.getenv(key):
        os.environ[key] = os.environ.get(key, "")

from api.services.api_manager import get_api_manager

conversation_history: Dict[str, List[Dict]] = {}

def extract_file_content(files: List[Dict[str, Any]]) -> str:
    content_parts = []
    
    for file in files:
        file_type = file.get("type", "")
        file_name = file.get("name", "unknown")
        file_data = file.get("data", "")
        
        if file_type == "text":
            content_parts.append(f"--- {file_name} ---\n{file_data[:8000]}\n")
        elif file_type == "pdf":
            try:
                import base64
                from io import BytesIO
                from pypdf import PdfReader
                
                pdf_bytes = base64.b64decode(file_data)
                pdf_file = BytesIO(pdf_bytes)
                reader = PdfReader(pdf_file)
                
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                
                if text.strip():
                    content_parts.append(f"--- {file_name} ---\n{text[:10000]}\n")
                else:
                    content_parts.append(f"--- {file_name} ---\n[No extractable text]\n")
            except Exception as e:
                content_parts.append(f"--- {file_name} ---\n[Error: {str(e)}]\n")
        elif file_type == "image":
            content_parts.append(f"--- {file_name} ---\n[Image uploaded]\n")
        elif file_type == "audio":
            content_parts.append(f"--- {file_name} ---\n[Audio uploaded]\n")
        elif file_type == "doc":
            try:
                import base64
                from io import BytesIO
                from docx import Document
                
                doc_bytes = base64.b64decode(file_data)
                doc_file = BytesIO(doc_bytes)
                doc = Document(doc_file)
                
                text = "\n".join([p.text for p in doc.paragraphs])
                if text.strip():
                    content_parts.append(f"--- {file_name} ---\n{text[:10000]}\n")
                else:
                    content_parts.append(f"--- {file_name} ---\n[Empty document]\n")
            except Exception as e:
                content_parts.append(f"--- {file_name} ---\n[Error: {str(e)}]\n")
        elif file_type == "pptx":
            content_parts.append(f"--- {file_name} ---\n[PowerPoint uploaded]\n")
    
    return "\n".join(content_parts)


def classify_query(message: str) -> tuple:
    msg = message.lower().strip()
    
    list_match = re.search(r'(?:\b(?:give|list|provide|show|write|tell|name|suggest|recommend|share|create|generate)\s+(?:me\s+)?(?:the\s+)?(\d+)\s+|(?:top|best|most\s+asked|most\s+common|most\s+popular|most\s+important|frequently\s+asked|common)\s+(\d+)\s+)', msg)
    if list_match:
        count = int(list_match.group(1) or list_match.group(2))
        return ("list", count)
    
    if any(w in msg for w in ["what is", "define", "explain", "describe", "how does", "why"]):
        return ("explain", 0)
    
    if any(w in msg for w in ["code", "function", "program", "script", "write a", "implement"]):
        return ("code", 0)
    
    if any(w in msg for w in ["compare", "difference between", "vs", "versus"]):
        return ("compare", 0)
    
    if any(w in msg for w in ["summarize", "summary", "brief", "short"]):
        return ("summarize", 0)
    
    if len(msg.split()) <= 5:
        return ("short", 0)
    
    return ("general", 0)


def build_prompt(message: str, history_text: str, extracted_content: str) -> tuple:
    query_type, list_count = classify_query(message)
    
    parts = []
    
    if extracted_content:
        parts.append(f"Document: {extracted_content[:8000]}")
    
    if history_text:
        parts.append(f"History: {history_text}")
    
    parts.append(f"Q: {message}")
    
    if query_type == "list":
        parts.append(f"Rules: Output exactly {list_count} items in this structured format:\n**Q.1 [question]?**\nAnswer: [concise answer with `keywords` in inline code]\n\n**Q.2 [question]?**\nAnswer: [concise answer with `keywords` in inline code]\n\n(continue up to Q.{list_count})\nStrictly keep Q and Answer on separate lines. Use bold for questions, inline code for technical terms. No intro/outro. Make answers complete and informative.")
        max_tokens = 4096
    elif query_type == "explain":
        parts.append("Rules: Direct answer first. Clear explanation with examples if helpful. Use bullets for multiple points.")
        max_tokens = 1500
    elif query_type == "code":
        parts.append("Rules: Show code first. Brief explanation after. No preamble.")
        max_tokens = 2048
    elif query_type == "compare":
        parts.append("Rules: Use comparison table or bullets. Highlight key differences. No intro.")
        max_tokens = 1200
    elif query_type == "summarize":
        parts.append("Rules: Clear summary. Key points with brief explanations.")
        max_tokens = 1000
    elif query_type == "short":
        parts.append("Rules: 1-2 sentence direct answer.")
        max_tokens = 300
    else:
        parts.append("Rules: Complete, helpful answer. Direct first. Bullets for lists. No filler.")
        max_tokens = 2048
    
    return "\n".join(parts), max_tokens


async def process_multimodal_query(message: str, user: str, files: List[Dict[str, Any]]) -> str:
    api_manager = get_api_manager()
    
    if user not in conversation_history:
        conversation_history[user] = []
    
    history = conversation_history[user]
    chat_messages = history[-6:]
    
    history_text = ""
    if chat_messages:
        history_text = "\n".join([f"U: {m['user'][:300]}\nA: {m['bot'][:500]}" for m in chat_messages])
    
    extracted_content = ""
    if files and len(files) > 0:
        extracted_content = extract_file_content(files)
    
    has_format_override = "STRICT REQUIREMENT" in message
    
    if has_format_override:
        prompt = f"Q: {message}\nRules: Follow instructions exactly. No filler."
        max_tokens = 1500
    else:
        prompt, max_tokens = build_prompt(message, history_text, extracted_content)
    
    answer = await api_manager.call_with_fallback(prompt, history_text, max_tokens)
    
    history.append({"user": message, "bot": answer})
    conversation_history[user] = history[-20:]
    
    return answer


def get_encouragement():
    encouragements = [
        "Every expert was once a beginner. I'm here to help you every step of the way!",
        "Great questions lead to great learning. Keep asking!",
        "You're building strong foundations for your CS journey!",
        "Learning is a journey, and I'm here to guide you."
    ]
    import random
    return random.choice(encouragements)


class DocumentProcessor:
    @staticmethod
    def process_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return splitter.split_text(text)
    
    @staticmethod
    def process_pdf_bytes(pdf_bytes: bytes) -> List[str]:
        try:
            from pypdf import PdfReader
            from io import BytesIO
            
            pdf_file = BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            
            return DocumentProcessor.process_text(text)
        except Exception as e:
            return [f"Error processing PDF: {str(e)}"]
    
    @staticmethod
    def summarize_text(text: str, max_words: int = 100) -> str:
        words = text.split()
        if len(words) <= max_words:
            return text
        
        summary = " ".join(words[:max_words])
        return summary + "... [truncated]"
