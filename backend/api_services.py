import os
import logging
import asyncio
from typing import List, Dict, Optional
import httpx
import openai
from anthropic import Anthropic
from dotenv import load_dotenv
from cache_manager import cached, APICache

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class PerplexityService:
    """Service for interacting with Perplexity Sonar API"""
    
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        if not self.api_key:
            logger.warning("PERPLEXITY_API_KEY not found in environment variables")
    
    @cached("perplexity_key_concepts", ttl=1800)  # 30 minutes cache
    async def get_key_concepts(self, topic: str, prompt: str) -> List[str]:
        """
        Get key concepts related to the topic and prompt using Perplexity Sonar
        """
        if not self.api_key:
            logger.error("Perplexity API key not available")
            raise ValueError("Perplexity API key is required but not found in environment variables")
        
        try:
            # Construct the research query
            research_query = f"""
            Based on the topic "{topic}" and the learning goal "{prompt}", 
            identify 6-8 key concepts that are essential for understanding this subject.
            
            Please provide a concise list of the most important concepts, principles, 
            or skills that someone should learn to master this topic.
            
            Format your response as a simple list, one concept per line.
            """
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a knowledgeable educational assistant that helps identify key learning concepts. Provide clear, concise responses."
                    },
                    {
                        "role": "user",
                        "content": research_query
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    # Parse the response to extract concepts
                    concepts = self._parse_concepts_from_response(content)
                    logger.info(f"Retrieved {len(concepts)} concepts from Perplexity")
                    return concepts
                else:
                    logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                    raise Exception(f"Perplexity API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Error calling Perplexity API: {e}")
            raise
    
    def _parse_concepts_from_response(self, content: str) -> List[str]:
        """Parse concepts from Perplexity response"""
        lines = content.strip().split('\n')
        concepts = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('*'):
                # Remove numbering and bullet points
                concept = line.lstrip('0123456789.-* ').strip()
                if concept and len(concept) > 3:  # Filter out very short items
                    concepts.append(concept)
        
        # Return up to 8 concepts
        return concepts[:8]
    


class LLMService:
    """Service for interacting with OpenAI and Anthropic APIs"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        else:
            logger.warning("OPENAI_API_KEY not found in environment variables")
        
        # Initialize Anthropic as backup
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=anthropic_api_key)
        else:
            logger.warning("ANTHROPIC_API_KEY not found in environment variables")
    
    @cached("llm_concept_explanations", ttl=3600)  # 1 hour cache
    async def generate_concept_explanations(self, key_concepts: List[str], topic: str, prompt: str) -> Dict[str, str]:
        """
        Generate explanations for each key concept using LLM
        """
        explanations = {}
        
        # PARALLEL PROCESSING: Generate explanations concurrently
        async def get_explanation(concept):
            try:
                return await self._get_concept_explanation(concept, topic, prompt)
            except Exception as e:
                logger.error(f"Error generating explanation for {concept}: {e}")
                return f"Brief explanation of {concept} in the context of {topic}. This concept is fundamental to understanding {prompt} and provides the foundation for advanced learning in this area."
        
        # Create tasks for all concepts
        tasks = [get_explanation(concept) for concept in key_concepts]
        
        # Process all concepts in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build explanations dictionary
        for i, concept in enumerate(key_concepts):
            if i < len(results) and not isinstance(results[i], Exception):
                explanations[concept] = results[i]
            else:
                explanations[concept] = f"Brief explanation of {concept} in the context of {topic}. This concept is fundamental to understanding {prompt} and provides the foundation for advanced learning in this area."
        
        return explanations
    
    @cached("llm_concept_summary", ttl=3600)  # 1 hour cache
    async def generate_concept_summary(self, key_concepts: List[str], topic: str, prompt: str) -> str:
        """
        Generate a comprehensive summary of the key concepts for Leo's first message
        """
        try:
            summary_prompt = f"""
            Based on the following learning context:
            - Topic: {topic}
            - Learning Goal: {prompt}
            - Key Concepts: {', '.join(key_concepts)}
            
            Create a comprehensive 2-3 paragraph summary that:
            1. Introduces the topic and its importance
            2. Explains how the key concepts relate to the learning goal
            3. Sets up an engaging learning journey
            
            This summary will be used by an AI assistant (Leo) to start a conversation with a learner.
            Make it encouraging, informative, and set up the learner for success.
            Keep it conversational and engaging.
            """
            
            response = await self._call_llm(summary_prompt, max_tokens=300)
            
            if response:
                return response.strip()
            else:
                return self._get_mock_summary(topic, prompt, key_concepts)
                
        except Exception as e:
            logger.error(f"Error generating concept summary: {e}")
            return self._get_mock_summary(topic, prompt, key_concepts)

    @cached("llm_learning_suggestions", ttl=3600)  # 1 hour cache
    async def generate_learning_suggestions(self, concept_explanations: Dict[str, str], topic: str, prompt: str) -> List[str]:
        """
        Generate personalized learning suggestions using LLM
        """
        try:
            suggestions_prompt = f"""
            Based on the following learning context:
            - Topic: {topic}
            - Learning Goal: {prompt}
            - Key Concepts: {', '.join(concept_explanations.keys())}
            
            Generate 6 personalized learning suggestions that will help someone effectively learn this topic.
            Focus on practical, actionable advice that considers the specific concepts and learning goal.
            
            Format as a numbered list of suggestions.
            """
            
            response = await self._call_llm(suggestions_prompt, max_tokens=400)
            
            if response:
                suggestions = self._parse_suggestions_from_response(response)
                return suggestions[:6]  # Return up to 6 suggestions
            else:
                return self._get_mock_suggestions(topic, prompt)
                
        except Exception as e:
            logger.error(f"Error generating learning suggestions: {e}")
            return self._get_mock_suggestions(topic, prompt)
    
    async def _get_concept_explanation(self, concept: str, topic: str, prompt: str) -> str:
        """Get explanation for a single concept"""
        explanation_prompt = f"""
        Provide a clear, concise explanation of "{concept}" in the context of learning {topic}.
        
        The learner's goal is: {prompt}
        
        Write 2-3 sentences that:
        1. Define what {concept} is
        2. Explain why it's important for this learning goal
        3. Give a brief practical context
        
        Keep it educational but accessible.
        """
        
        response = await self._call_llm(explanation_prompt, max_tokens=150)
        return response or f"Brief explanation of {concept} in the context of {topic}. This concept is fundamental to understanding {prompt} and provides the foundation for advanced learning in this area."
    
    async def _call_llm(self, prompt: str, max_tokens: int = 200) -> Optional[str]:
        """Call the available LLM service"""
        # Try OpenAI first
        if self.openai_client:
            try:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful educational assistant that provides clear, concise explanations."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
        
        # Fallback to Anthropic
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text.strip()
            except Exception as e:
                logger.error(f"Anthropic API error: {e}")
        
        return None
    
    def _parse_suggestions_from_response(self, content: str) -> List[str]:
        """Parse learning suggestions from LLM response"""
        lines = content.strip().split('\n')
        suggestions = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                # Remove numbering and bullet points
                suggestion = line.lstrip('0123456789.-* ').strip()
                if suggestion and len(suggestion) > 10:  # Filter out very short items
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _get_mock_summary(self, topic: str, prompt: str, key_concepts: List[str]) -> str:
        """Fallback mock summary when LLM is not available"""
        concepts_text = ", ".join(key_concepts[:3])  # Show first 3 concepts
        return f"""Welcome to your learning journey in {topic}! 

This is an exciting field that will help you achieve your goal: {prompt}. We've identified key concepts like {concepts_text} that are essential for mastering this topic. These concepts form the foundation of your learning path and will guide you toward success.

I'm here to help you explore these concepts, answer your questions, and provide hands-on examples. How would you like to start learning? Would you prefer to dive into the fundamentals, work on a practical project, or explore a specific concept that interests you most?"""

    def _get_mock_suggestions(self, topic: str, prompt: str) -> List[str]:
        """Fallback mock suggestions when LLM is not available"""
        return [
            f"Start with the fundamentals of {topic} to build a strong foundation",
            "Practice with hands-on coding exercises and projects",
            "Join online communities and forums for peer learning",
            "Create a personal project to apply what you learn",
            "Set up a study schedule with regular review sessions",
            "Find a mentor or study group for guidance and motivation"
        ]


# Global service instances
perplexity_service = PerplexityService()
llm_service = LLMService()
