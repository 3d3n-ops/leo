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
    AI Assistant Service for Threads.io
    Features tool calling capabilities
    """
    
    # Model-specific optimizations - Updated with Groq models through OpenRouter
    MODEL_CONFIGS = {
        # Groq models (ultra-fast)
        "moonshotai/kimi-k2-0905": {
            "max_tokens": 2000,
            "temperature": 0.6,
            "timeout": 8.0,
            "priority": "ultra_high"
        },
        "openai/gpt-oss-120b": {
            "max_tokens": 2000,
            "temperature": 0.7,
            "timeout": 10.0,
            "priority": "high"
        },
        "meta-llama/llama-guard-4-12b": {
            "max_tokens": 1500,
            "temperature": 0.5,
            "timeout": 6.0,
            "priority": "ultra_high"
        },
        "deepseek/deepseek-r1-distill-llama-70b": {
            "max_tokens": 2000,
            "temperature": 0.6,
            "timeout": 8.0,
            "priority": "high"
        },
        "google/gemma-2-9b-it": {
            "max_tokens": 1500,
            "temperature": 0.6,
            "timeout": 5.0,
            "priority": "ultra_high"
        },
        # Original models (fallback)
        "deepseek/deepseek-chat-v3.1": {
            "max_tokens": 1500,
            "temperature": 0.6,
            "timeout": 30.0,
            "priority": "medium"
        },
        "openai/gpt-5": {
            "max_tokens": 2000,
            "temperature": 0.7,
            "timeout": 45.0,
            "priority": "medium"
        },
        "anthropic/claude-sonnet-4": {
            "max_tokens": 2000,
            "temperature": 0.7,
            "timeout": 50.0,
            "priority": "low"
        },
        "google/gemini-2.5-pro": {
            "max_tokens": 1500,
            "temperature": 0.6,
            "timeout": 60.0,
            "priority": "low"
        },
        "qwen/qwen3-coder": {
            "max_tokens": 1800,
            "temperature": 0.6,
            "timeout": 40.0,
            "priority": "medium"
        },
        "x-ai/grok-code-fast-1": {
            "max_tokens": 1500,
            "temperature": 0.6,
            "timeout": 35.0,
            "priority": "medium"
        }
    }
    
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.perplexity_base_url = "https://api.perplexity.ai/chat/completions"
        
        if not self.openrouter_api_key:
            logger.warning("OPENROUTER_API_KEY not found in environment variables")
        
        # Leo's system prompt v1
        self.system_prompt = """You are Leo, an AI assistant specialized in helping people learn programming, mathematics/STEM, and software engineering concepts. 
You are knowledgeable, patient, and encouraging.

## Core Behavior
- Always explain concepts in a clear, step-by-step way with practical examples.
- Be supportive and conversational to keep learners engaged.
- When appropriate, call one of your tools instead of generating plain text.
- After calling a tool, explain the result to the learner in natural language.

## Available Tools
1. `write_code(language, code, explanation, use_case)` - generate code with comments and explanations
2. `write_math(formula, explanation, steps, context)` - return math in LaTeX with reasoning
3. `write_diagrams(diagram_type, mermaid_code, description, learning_points)` - create visual diagrams in Mermaid
4. `write_quiz(question, options, correct_answer, explanation, difficulty)` - create quizzes with multiple choice answers
5. `use_rag_search(query, reason)` - search in uploaded documents
6. `use_web_search(query, reason)` - search the web for current information

## How to Decide When to Use Tools
- If the user asks for code → call `write_code`
- If the user asks to solve or explain a math problem → call `write_math`
- If the user asks for a diagram, flowchart, or visualization → call `write_diagrams`
- If the user asks for practice questions, tests, or quizzes → call `write_quiz`
- If the user refers to uploaded files or documents → call `use_rag_search`
- If the user asks about real-time info, news, or the “latest” version of something → call `use_web_search`
- Always prefer tools when they add clarity, structure, or interactivity to the learning process.

## Examples
**Example 1 - Code**
User: "Can you show me a Python function that reverses a string?"
Assistant: (call `write_code` with language="python", code="...", explanation="...", use_case="...")

**Example 2 - Math**
User: "How do I solve quadratic equations?"
Assistant: (call `write_math` with formula="x = (-b ± √(b^2 - 4ac)) / 2a", explanation="...", steps="...", context="...")

**Example 3 - Diagram**
User: "Can you draw me a flowchart for a login process?"
Assistant: (call `write_diagrams` with diagram_type="flowchart", mermaid_code="...", description="...", learning_points="...")

**Example 4 - Quiz**
User: "Give me a quiz question about binary search."
Assistant: (call `write_quiz` with question="...", options=["A", "B", "C", "D"], correct_answer="B", explanation="...", difficulty="intermediate")

**Example 5 - RAG Search**
User: "What did the uploaded document say about climate policy?"
Assistant: (call `use_rag_search` with query="climate policy", reason="The user asked about content inside uploaded documents.")

**Example 6 - Web Search**
User: "What's the latest version of Python right now?"
Assistant: (call `use_web_search` with query="latest version of Python", reason="The user asked for current info.")

---

Remember: Always respond in a warm, encouraging way, and after a tool call, explain the results in natural language so the learner understands them.
"""

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

            # Stream response directly - tool calls will be handled in streaming
            async for chunk in self._stream_chat_response_with_tools(messages, model, use_rag, use_web_search, rag_documents):
                yield chunk

        except Exception as e:
            logger.error(f"Error in Leo chat: {e}")
            yield json.dumps({"error": str(e)})

    async def _check_for_tool_calls(self, messages: List[Dict], model: str) -> Optional[Dict]:
        """Check if the response contains tool calls using a non-streaming request"""
        try:
            # Get model-specific configuration
            config = self.MODEL_CONFIGS.get(model, {})
            
            payload = {
                "model": model,
                "messages": messages,
                "tools": self.tools,
                "tool_choice": "auto",
                "stream": False,
                "temperature": config.get("temperature", 0.7),
                "max_tokens": config.get("max_tokens", 2000)
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

    async def _stream_chat_response_with_tools(
        self, 
        messages: List[Dict], 
        model: str, 
        use_rag: bool, 
        use_web_search: bool, 
        rag_documents: Optional[List[Dict]]
    ) -> AsyncGenerator[str, None]:
        """Stream chat response with tool call support"""
        try:
            # Get model-specific configuration
            config = self.MODEL_CONFIGS.get(model, {})
            
            payload = {
                "model": model,
                "messages": messages,
                "tools": self.tools,
                "tool_choice": "auto",
                "stream": True,
                "temperature": config.get("temperature", 0.7),
                "max_tokens": config.get("max_tokens", 2000)
            }

            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://docs-wiki.vercel.app",
                "X-Title": "Docs Wiki - Leo AI Assistant"
            }

            # Use optimized timeout
            timeout = config.get("timeout", 60.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
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

                    # Track tool calls being built
                    current_tool_calls = {}
                    
                    # Process streaming response
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            
                            if data.strip() == "[DONE]":
                                # Process any remaining tool calls
                                for tool_call in current_tool_calls.values():
                                    if tool_call["name"]:
                                        try:
                                            # Parse accumulated arguments
                                            args = json.loads(tool_call["arguments"]) if tool_call["arguments"] else {}
                                        except json.JSONDecodeError:
                                            args = {}
                                        
                                        if tool_call["name"] in ["write_code", "write_math", "write_diagrams", "write_quiz"]:
                                            yield json.dumps({
                                                "tool_call": {
                                                    "name": tool_call["name"],
                                                    "arguments": args
                                                }
                                            })
                                        elif tool_call["name"] == "use_rag_search" and use_rag and rag_documents:
                                            search_result = self._simulate_rag_search(args.get("query", ""), rag_documents)
                                            yield json.dumps({
                                                "tool_call": {
                                                    "name": tool_call["name"],
                                                    "arguments": args,
                                                    "result": search_result
                                                }
                                            })
                                        elif tool_call["name"] == "use_web_search" and use_web_search:
                                            yield json.dumps({
                                                "tool_call": {
                                                    "name": tool_call["name"],
                                                    "arguments": args,
                                                    "result": "Web search capability available (implementation needed)"
                                                }
                                            })
                                break
                            
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    choice = chunk["choices"][0]
                                    
                                    # Handle tool calls
                                    if "delta" in choice and "tool_calls" in choice["delta"]:
                                        tool_calls = choice["delta"]["tool_calls"]
                                        for tool_call in tool_calls:
                                            tool_call_index = tool_call.get("index", 0)
                                            
                                            # Initialize tool call if not exists
                                            if tool_call_index not in current_tool_calls:
                                                current_tool_calls[tool_call_index] = {
                                                    "name": "",
                                                    "arguments": "",
                                                    "id": tool_call.get("id", "")
                                                }
                                            
                                            # Update tool call data
                                            if "function" in tool_call:
                                                if "name" in tool_call["function"]:
                                                    current_tool_calls[tool_call_index]["name"] = tool_call["function"]["name"]
                                                if "arguments" in tool_call["function"]:
                                                    current_tool_calls[tool_call_index]["arguments"] += tool_call["function"]["arguments"]
                                    
                                    # Handle regular content
                                    elif "delta" in choice and "content" in choice["delta"]:
                                        content = choice["delta"]["content"]
                                        if content:
                                            yield json.dumps({"content": content})
                            
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            logger.error(f"Error streaming chat response with tools: {e}")
            yield json.dumps({"error": str(e)})

    async def _stream_chat_response(self, messages: List[Dict], model: str) -> AsyncGenerator[str, None]:
        """Stream a regular chat response without tool calls"""
        try:
            # Get model-specific configuration
            config = self.MODEL_CONFIGS.get(model, {})
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
                "temperature": config.get("temperature", 0.7),
                "max_tokens": config.get("max_tokens", 2000)
            }

            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://docs-wiki.vercel.app",
                "X-Title": "Docs Wiki - Leo AI Assistant"
            }

            # Use optimized timeout
            timeout = config.get("timeout", 60.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
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

                    # Optimize streaming with buffering for better performance
                    buffer = ""
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            
                            if data.strip() == "[DONE]":
                                # Flush any remaining buffer
                                if buffer.strip():
                                    try:
                                        chunk = json.loads(buffer)
                                        if "choices" in chunk and len(chunk["choices"]) > 0:
                                            choice = chunk["choices"][0]
                                            if "delta" in choice and "content" in choice["delta"]:
                                                content = choice["delta"]["content"]
                                                if content:
                                                    yield json.dumps({"content": content})
                                    except json.JSONDecodeError:
                                        pass
                                break
                            
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    choice = chunk["choices"][0]
                                    if "delta" in choice and "content" in choice["delta"]:
                                        content = choice["delta"]["content"]
                                        if content:
                                            # Yield immediately for better perceived performance
                                            yield json.dumps({"content": content})
                            except json.JSONDecodeError:
                                # Buffer incomplete JSON for next iteration
                                buffer = data
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
                if function_args is None:
                    args = {}
                elif isinstance(function_args, dict):
                    # Already parsed
                    args = function_args
                elif isinstance(function_args, str):
                    try:
                        args = json.loads(function_args)
                    except Exception:
                        # As a fallback, try to coerce to JSON by fixing common issues
                        try:
                            sanitized = function_args.replace("\n", "\\n")
                            args = json.loads(sanitized)
                        except Exception:
                            logger.warning(f"Failed to parse tool call arguments: {function_args}")
                            args = {"raw_arguments": function_args}
                else:
                    # Unexpected type
                    logger.warning(f"Unexpected type for tool call arguments: {type(function_args)}")
                    args = {"raw_arguments": str(function_args)}
                
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

    async def generate_first_message(self, concept_summary: str, key_concepts: List[str], topic: str) -> str:
        """
        Generate Leo's first message based on the concept summary and key concepts
        """
        try:
            first_message_prompt = f"""
            You are Leo, an AI learning assistant. Based on this research summary about {topic}:

            {concept_summary}

            Key concepts identified: {', '.join(key_concepts)}

            Generate a warm, engaging first message to start a learning conversation. The message should:
            1. Acknowledge the learner's interest in {topic}
            2. Reference the key concepts naturally
            3. Ask how they'd like to continue learning
            4. Be encouraging and supportive
            5. Keep it conversational and not too long (2-3 sentences)

            Make it feel like you're excited to help them learn!
            """
            
            response = await self._call_leo_llm(first_message_prompt, max_tokens=150)
            
            if response:
                return response.strip()
            else:
                return self._get_mock_first_message(topic, key_concepts)
                
        except Exception as e:
            logger.error(f"Error generating first message: {e}")
            return self._get_mock_first_message(topic, key_concepts)

    async def _call_leo_llm(self, prompt: str, max_tokens: int = 200) -> Optional[str]:
        """Call the LLM service for Leo's responses using fastest Groq model"""
        try:
            payload = {
                "model": "google/gemma-2-9b-it",  # Ultra-fast Groq model
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are Leo, an enthusiastic AI learning assistant. Be encouraging, helpful, and conversational."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.8,
                "stream": False
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
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    logger.error(f"Leo LLM API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling Leo LLM: {e}")
            return None

    def _get_mock_first_message(self, topic: str, key_concepts: List[str]) -> str:
        """Fallback first message when LLM is not available"""
        concepts_text = ", ".join(key_concepts[:3])
        return f"Hi there! I'm Leo, your AI learning assistant. I'm excited to help you explore {topic}! I've identified some key concepts like {concepts_text} that we can dive into. How would you like to start your learning journey?"

    async def chat_with_leo(
        self, 
        message: str, 
        model: str, 
        rag_documents: Optional[List[Dict]] = None, 
        use_rag: bool = False, 
        use_web_search: bool = False
    ) -> AsyncGenerator[str, None]:
        """Main chat method that handles both regular chat and tool calls"""
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Add RAG context if available
            if use_rag and rag_documents:
                rag_context = self._format_rag_context(rag_documents)
                if rag_context:
                    messages.append({
                        "role": "system", 
                        "content": f"Additional context from uploaded documents:\n\n{rag_context}"
                    })
            
            # Use streaming with tools
            async for chunk in self._stream_chat_response_with_tools(
                messages=messages,
                model=model,
                use_rag=use_rag,
                use_web_search=use_web_search,
                rag_documents=rag_documents
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in chat_with_leo: {e}")
            yield json.dumps({"error": str(e)})


# Global Leo service instance
leo_service = LeoService()
