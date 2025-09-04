import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LeoService:
    """
    Leo AI Assistant Service - A dynamic AI agent for programming, math/STEM, and software engineering education.
    Features tool calling capabilities and optional RAG/web search integration.
    """
    
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.perplexity_base_url = "https://api.perplexity.ai/chat/completions"
        
        if not self.openrouter_api_key:
            logger.warning("OPENROUTER_API_KEY not found in environment variables")
        
        # Leo's system prompt
        self.system_prompt = """You are Leo, an AI assistant specialized in helping people learn programming, mathematics/STEM, and software engineering/computer science concepts. You are knowledgeable, patient, and encouraging.

Your capabilities include:
1. **write_code**: Generate code snippets in any programming language with explanations
2. **write_math**: Generate mathematical formulas and work in LaTeX format with proper rendering
3. **write_diagrams**: Create diagrams using Mermaid syntax for visual learning
4. **write_quiz**: Generate quizzes with questions and multiple choice answers

When responding to users:
- Be encouraging and supportive
- Break down complex concepts into digestible parts
- Provide practical examples and real-world applications
- Use your tools when appropriate to enhance learning
- If you need current information or the user asks about specific files/URLs that were uploaded, consider using RAG or web search
- Always explain your reasoning and provide context

Remember: Your goal is to make learning accessible, engaging, and effective for everyone."""

        # Tool definitions for function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "write_code",
                    "description": "Generate code snippets in any programming language with explanations and comments",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "language": {
                                "type": "string",
                                "description": "Programming language (e.g., python, javascript, java, c++, etc.)"
                            },
                            "code": {
                                "type": "string",
                                "description": "The code snippet to generate"
                            },
                            "explanation": {
                                "type": "string",
                                "description": "Explanation of what the code does and how it works"
                            },
                            "use_case": {
                                "type": "string",
                                "description": "When and why you would use this code"
                            }
                        },
                        "required": ["language", "code", "explanation"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_math",
                    "description": "Generate mathematical formulas and work in LaTeX format with proper rendering",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "formula": {
                                "type": "string",
                                "description": "The mathematical formula or equation in LaTeX format"
                            },
                            "explanation": {
                                "type": "string",
                                "description": "Explanation of the mathematical concept and how to solve it"
                            },
                            "steps": {
                                "type": "string",
                                "description": "Step-by-step solution process (optional)"
                            },
                            "context": {
                                "type": "string",
                                "description": "When and where this mathematical concept is used"
                            }
                        },
                        "required": ["formula", "explanation"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_diagrams",
                    "description": "Create diagrams using Mermaid syntax for visual learning",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "diagram_type": {
                                "type": "string",
                                "description": "Type of diagram (flowchart, sequence, class, etc.)"
                            },
                            "mermaid_code": {
                                "type": "string",
                                "description": "Mermaid diagram code"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of what the diagram shows"
                            },
                            "learning_points": {
                                "type": "string",
                                "description": "Key learning points from the diagram"
                            }
                        },
                        "required": ["diagram_type", "mermaid_code", "description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_quiz",
                    "description": "Generate quizzes with questions and multiple choice answers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The quiz question"
                            },
                            "options": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Multiple choice options (A, B, C, D)"
                            },
                            "correct_answer": {
                                "type": "string",
                                "description": "The correct answer (A, B, C, or D)"
                            },
                            "explanation": {
                                "type": "string",
                                "description": "Explanation of why the correct answer is right"
                            },
                            "difficulty": {
                                "type": "string",
                                "enum": ["beginner", "intermediate", "advanced"],
                                "description": "Difficulty level of the question"
                            }
                        },
                        "required": ["question", "options", "correct_answer", "explanation"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "use_rag_search",
                    "description": "Search through uploaded documents/files for relevant information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for the RAG system"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Why you need to search the uploaded documents"
                            }
                        },
                        "required": ["query", "reason"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "use_web_search",
                    "description": "Search the web for current information using Perplexity",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for web search"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Why you need current web information"
                            }
                        },
                        "required": ["query", "reason"]
                    }
                }
            }
        ]

    async def chat_with_leo(
        self, 
        message: str, 
        model: str,
        rag_documents: Optional[List[Dict]] = None,
        use_rag: bool = False,
        use_web_search: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Chat with Leo AI assistant with optional RAG and web search capabilities
        """
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message}
            ]

            # Add RAG context if available and requested
            if use_rag and rag_documents:
                rag_context = self._format_rag_context(rag_documents)
                messages.append({
                    "role": "system", 
                    "content": f"Relevant context from uploaded documents:\n{rag_context}"
                })

            # First, make a non-streaming request to check for tool calls
            tool_call_response = await self._check_for_tool_calls(messages, model)
            
            if tool_call_response and "tool_calls" in tool_call_response:
                # Handle tool calls with non-streaming approach
                async for chunk in self._handle_tool_calls_non_streaming(tool_call_response, use_rag, use_web_search, rag_documents):
                    yield chunk
            else:
                # Stream regular chat response
                async for chunk in self._stream_chat_response(messages, model):
                    yield chunk

        except Exception as e:
            logger.error(f"Error in Leo chat: {e}")
            yield json.dumps({"error": str(e)})

    async def _check_for_tool_calls(self, messages: List[Dict], model: str) -> Optional[Dict]:
        """Check if the response contains tool calls using a non-streaming request"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "tools": self.tools,
                "tool_choice": "auto",
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 2000
            }

            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://docs-wiki.vercel.app",
                "X-Title": "Docs Wiki - Leo AI Assistant"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.openrouter_base_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        choice = data["choices"][0]
                        if "message" in choice:
                            return choice["message"]
                
                return None
                
        except Exception as e:
            logger.error(f"Error checking for tool calls: {e}")
            return None

    async def _stream_chat_response(self, messages: List[Dict], model: str) -> AsyncGenerator[str, None]:
        """Stream a regular chat response without tool calls"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 2000
            }

            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://docs-wiki.vercel.app",
                "X-Title": "Docs Wiki - Leo AI Assistant"
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    self.openrouter_base_url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"OpenRouter API error: {response.status_code} - {error_text}")
                        yield json.dumps({"error": f"API error: {response.status_code}"})
                        return

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            
                            if data.strip() == "[DONE]":
                                break
                            
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    choice = chunk["choices"][0]
                                    if "delta" in choice and "content" in choice["delta"]:
                                        content = choice["delta"]["content"]
                                        if content:
                                            yield json.dumps({"content": content})
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            logger.error(f"Error streaming chat response: {e}")
            yield json.dumps({"error": str(e)})

    async def _handle_tool_calls_non_streaming(
        self, 
        message: Dict, 
        use_rag: bool, 
        use_web_search: bool, 
        rag_documents: Optional[List[Dict]]
    ) -> AsyncGenerator[str, None]:
        """Handle tool calls using non-streaming approach"""
        try:
            if "tool_calls" not in message:
                return
            
            for tool_call in message["tool_calls"]:
                function_name = tool_call.get("function", {}).get("name")
                function_args = tool_call.get("function", {}).get("arguments", "{}")
                
                # Parse arguments
                args = {}
                if function_args:
                    try:
                        args = json.loads(function_args)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse tool call arguments: {function_args}")
                        args = {"raw_arguments": function_args}
                
                # Handle different tool calls
                if function_name == "write_code":
                    yield json.dumps({
                        "tool_call": {
                            "name": function_name,
                            "arguments": args
                        }
                    })
                elif function_name == "write_math":
                    yield json.dumps({
                        "tool_call": {
                            "name": function_name,
                            "arguments": args
                        }
                    })
                elif function_name == "write_diagrams":
                    yield json.dumps({
                        "tool_call": {
                            "name": function_name,
                            "arguments": args
                        }
                    })
                elif function_name == "write_quiz":
                    yield json.dumps({
                        "tool_call": {
                            "name": function_name,
                            "arguments": args
                        }
                    })
                elif function_name == "use_rag_search" and use_rag and rag_documents:
                    search_result = self._simulate_rag_search(args.get("query", ""), rag_documents)
                    yield json.dumps({
                        "tool_call": {
                            "name": function_name,
                            "arguments": args,
                            "result": search_result
                        }
                    })
                elif function_name == "use_web_search" and use_web_search:
                    yield json.dumps({
                        "tool_call": {
                            "name": function_name,
                            "arguments": args,
                            "result": "Web search capability available (implementation needed)"
                        }
                    })
                
        except Exception as e:
            logger.error(f"Error handling tool calls: {e}")
            yield json.dumps({"error": str(e)})


    def _format_rag_context(self, rag_documents: List[Dict]) -> str:
        """Format RAG documents into context for Leo"""
        if not rag_documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(rag_documents[:5]):  # Limit to 5 most relevant docs
            content = doc.get("text", "")[:500]  # Limit content length
            source = doc.get("metadata", {}).get("source", f"Document {i+1}")
            context_parts.append(f"Source: {source}\nContent: {content}\n")
        
        return "\n".join(context_parts)

    def _simulate_rag_search(self, query: str, rag_documents: List[Dict]) -> str:
        """Simulate RAG search (placeholder for actual RAG implementation)"""
        # This is a simple simulation - in real implementation, you'd use your vector store
        relevant_docs = []
        query_lower = query.lower()
        
        for doc in rag_documents:
            content = doc.get("text", "").lower()
            if any(word in content for word in query_lower.split()):
                relevant_docs.append(doc)
        
        if relevant_docs:
            return f"Found {len(relevant_docs)} relevant documents for query: '{query}'"
        else:
            return f"No relevant documents found for query: '{query}'"

    async def web_search(self, query: str) -> str:
        """Perform web search using Perplexity API"""
        if not self.perplexity_api_key:
            return "Web search not available - API key not configured"
        
        try:
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful research assistant. Provide concise, accurate information."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.perplexity_base_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error(f"Perplexity API error: {response.status_code}")
                    return f"Web search error: {response.status_code}"
                    
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return f"Web search error: {str(e)}"

    def should_use_rag(self, message: str, has_uploaded_files: bool = False) -> bool:
        """Determine if RAG should be used based on the message and context"""
        if not has_uploaded_files:
            return False
        
        # Keywords that suggest RAG might be useful
        rag_keywords = [
            "document", "file", "uploaded", "reference", "according to", 
            "based on", "from the", "in the document", "what does it say",
            "summarize", "extract", "find in", "search in"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in rag_keywords)

    def should_use_web_search(self, message: str) -> bool:
        """Determine if web search should be used based on the message"""
        # Keywords that suggest current information is needed
        web_keywords = [
            "current", "latest", "recent", "today", "now", "2024", "2025",
            "news", "update", "what's new", "recently", "latest version",
            "current state", "nowadays", "these days"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in web_keywords)


# Global Leo service instance
leo_service = LeoService()
