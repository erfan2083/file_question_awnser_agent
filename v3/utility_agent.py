"""Utility Agent for supportive tasks like translation, summarization, and checklist generation."""

from typing import Any, Dict

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

from src.config.settings import settings
from src.models.schemas import AgentState, AgentType, UtilityTask


class UtilityAgent:
    """Agent responsible for utility tasks."""

    def __init__(self):
        """Initialize Utility Agent."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=0.3,
            max_output_tokens=settings.max_output_tokens,
            google_api_key=settings.google_api_key,
        )

        # Create task-specific prompts
        self.prompts = self._create_prompts()

    def _create_prompts(self) -> Dict[str, PromptTemplate]:
        """
        Create prompt templates for different utility tasks.

        Returns:
            Dictionary of task name to PromptTemplate
        """
        prompts = {}

        # Translation prompt
        prompts["translate"] = PromptTemplate(
            input_variables=["text", "target_language"],
            template="""Translate the following text to {target_language}. 
Maintain the original meaning, tone, and formatting.

Text to translate:
{text}

Translation:""",
        )

        # Summarization prompt
        prompts["summarize"] = PromptTemplate(
            input_variables=["text"],
            template="""Provide a concise summary of the following text. 
Capture the main points and key information.

Text to summarize:
{text}

Summary:""",
        )

        # Checklist generation prompt
        prompts["checklist"] = PromptTemplate(
            input_variables=["text"],
            template="""Based on the following text, create a structured checklist of action items or key points.
Format each item as a checkbox item.

Text:
{text}

Checklist:""",
        )

        # Keyword extraction prompt
        prompts["extract_keywords"] = PromptTemplate(
            input_variables=["text"],
            template="""Extract the most important keywords and key phrases from the following text.
List them in order of importance.

Text:
{text}

Keywords:""",
        )

        return prompts

    def execute(
        self, task: UtilityTask, text: str, **kwargs
    ) -> AgentState:
        """
        Execute a utility task.

        Args:
            task: Type of utility task
            text: Input text
            **kwargs: Additional task-specific parameters

        Returns:
            AgentState with task result
        """
        logger.info(f"Utility Agent executing task: {task.value}")

        try:
            if task == UtilityTask.TRANSLATE:
                result = self._translate(text, kwargs.get("target_language", "es"))
            elif task == UtilityTask.SUMMARIZE:
                result = self._summarize(text)
            elif task == UtilityTask.CHECKLIST:
                result = self._generate_checklist(text)
            elif task == UtilityTask.EXTRACT_KEYWORDS:
                result = self._extract_keywords(text)
            else:
                raise ValueError(f"Unknown utility task: {task}")

            state = AgentState(
                agent_type=AgentType.UTILITY,
                input_data={"task": task.value, "text_length": len(text)},
                output_data={"result": result, "task": task.value},
                metadata={"status": "success"},
            )

            logger.info(f"Utility Agent completed task: {task.value}")

            return state

        except Exception as e:
            logger.error(f"Error in Utility Agent execution: {e}")
            return AgentState(
                agent_type=AgentType.UTILITY,
                input_data={"task": task.value},
                output_data={},
                error=str(e),
                metadata={"status": "error"},
            )

    def _translate(self, text: str, target_language: str) -> str:
        """
        Translate text to target language.

        Args:
            text: Text to translate
            target_language: Target language code or name

        Returns:
            Translated text
        """
        chain = LLMChain(llm=self.llm, prompt=self.prompts["translate"])
        response = chain.invoke({"text": text, "target_language": target_language})
        return response["text"].strip()

    def _summarize(self, text: str) -> str:
        """
        Summarize text.

        Args:
            text: Text to summarize

        Returns:
            Summary text
        """
        chain = LLMChain(llm=self.llm, prompt=self.prompts["summarize"])
        response = chain.invoke({"text": text})
        return response["text"].strip()

    def _generate_checklist(self, text: str) -> str:
        """
        Generate checklist from text.

        Args:
            text: Text to convert to checklist

        Returns:
            Checklist text
        """
        chain = LLMChain(llm=self.llm, prompt=self.prompts["checklist"])
        response = chain.invoke({"text": text})
        return response["text"].strip()

    def _extract_keywords(self, text: str) -> str:
        """
        Extract keywords from text.

        Args:
            text: Text to extract keywords from

        Returns:
            Keywords text
        """
        chain = LLMChain(llm=self.llm, prompt=self.prompts["extract_keywords"])
        response = chain.invoke({"text": text})
        return response["text"].strip()

    def translate_answer(self, answer: str, target_language: str) -> str:
        """
        Translate an answer to a different language.

        Args:
            answer: Answer text to translate
            target_language: Target language

        Returns:
            Translated answer
        """
        return self._translate(answer, target_language)

    def summarize_document(self, document_text: str, max_length: int = 200) -> str:
        """
        Summarize a document with optional length constraint.

        Args:
            document_text: Full document text
            max_length: Maximum words in summary

        Returns:
            Document summary
        """
        # Add length constraint to prompt
        custom_prompt = PromptTemplate(
            input_variables=["text", "max_length"],
            template="""Provide a concise summary of the following text in approximately {max_length} words.
Capture the main points and key information.

Text:
{text}

Summary:""",
        )

        chain = LLMChain(llm=self.llm, prompt=custom_prompt)
        response = chain.invoke({"text": document_text, "max_length": max_length})
        return response["text"].strip()

    def create_action_checklist(
        self, document_text: str, context: str = ""
    ) -> str:
        """
        Create an action-oriented checklist from document.

        Args:
            document_text: Document text
            context: Optional context for checklist creation

        Returns:
            Action checklist
        """
        custom_prompt = PromptTemplate(
            input_variables=["text", "context"],
            template="""Based on the following text, create a structured checklist of actionable items.
{context}

Format each item as:
- [ ] Action item description

Text:
{text}

Action Checklist:""",
        )

        chain = LLMChain(llm=self.llm, prompt=custom_prompt)
        response = chain.invoke(
            {"text": document_text, "context": context or "Focus on actionable tasks."}
        )
        return response["text"].strip()
