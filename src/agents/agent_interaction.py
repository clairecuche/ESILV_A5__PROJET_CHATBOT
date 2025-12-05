from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from src.agents.prompts import prompts
import logging

logger = logging.getLogger(__name__)


class AgentInteraction:
    def __init__(self):
        self.llm = ChatOllama(
            model="mistral",
            temperature=0.7
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", prompts.INTERACTION_AGENT_SYSTEM),
            ("human", "{message}")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
        
        self.quick_responses = {
            'bonjour': prompts.INTERACTION_GREETING,
            'salut': prompts.INTERACTION_GREETING,
            'hello': prompts.INTERACTION_GREETING,
            'hey': prompts.INTERACTION_GREETING,
            'merci': prompts.INTERACTION_THANKS,
            'thanks': prompts.INTERACTION_THANKS,
            'au revoir': prompts.INTERACTION_GOODBYE,
            'bye': prompts.INTERACTION_GOODBYE,
            'adieu': prompts.INTERACTION_GOODBYE
        }
        
        logger.info("Agent Interaction initialisé")
    
    def run(self, message: str) -> str:
        message_lower = message.lower().strip()
        
        for keyword, response in self.quick_responses.items():
            if message_lower == keyword or message_lower.startswith(keyword + ' '):
                logger.info(f"Réponse rapide pour: {keyword}")
                return response
        
        try:
            logger.info(f"Génération réponse pour: {message[:50]}...")
            response = self.chain.invoke({"message": message})
            logger.info(f"Réponse générée: {response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"Erreur Agent Interaction: {e}")
            return prompts.INTERACTION_CLARIFICATION