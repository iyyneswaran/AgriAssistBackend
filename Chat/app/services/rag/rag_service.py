from google import genai
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from app.db.models.user import User
from app.core.config import settings

from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.retriever import Retriever


class RagService:
    """
    Orchestrates RAG pipeline for scheme recommendation.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.retriever = Retriever()
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

    async def build_user_context(self, user: User) -> str:
        """
        Build structured context string for embedding.
        """

        context_parts = [
            f"Farmer region: {user.region}",
            f"Primary crop: {user.crop_type}",
            f"Land size: {user.land_size} acres",
        ]

        return "\n".join(context_parts)

    async def recommend_schemes(
        self,
        query: str,
        user: User,
        db: AsyncSession,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Full RAG flow:
        1. Build user context
        2. Embed query + context
        3. Retrieve similar schemes
        4. Apply ranking/filtering
        5. Generate final answer with LLM using retrieved context
        """

        # 1️⃣ Build contextual query
        user_context = await self.build_user_context(user)

        enriched_query = f"""
        User Query:
        {query}

        Farmer Context:
        {user_context}

        Recommend relevant agricultural schemes.
        """

        # 2️⃣ Generate embedding
        embedding = await self.embedding_service.embed_text(enriched_query)

        # 3️⃣ Retrieve from vector store
        results = await self.retriever.retrieve(
            embedding=embedding,
            top_k=top_k,
        )

        # 4️⃣ Post-filtering / ranking (optional logic)
        ranked_results = self._rank_results(results, user)

        # 5️⃣ Generate Final Answer using context
        context_text = self._build_retrieved_context(ranked_results)
        final_answer = await self._generate_answer(query, user_context, context_text)

        return {
            "answer": final_answer,
            "source_documents": ranked_results
        }

    def _rank_results(self, results: List[dict], user: User) -> List[dict]:
        """
        Additional scoring layer based on region & crop match.
        """

        for item in results:
            score = item.get("similarity", 0)

            if item.get("region") == user.region:
                score += 0.05

            if item.get("crop_type") == user.crop_type:
                score += 0.05

            item["final_score"] = round(score, 4)

        return sorted(results, key=lambda x: x["final_score"], reverse=True)

    def _build_retrieved_context(self, results: List[dict]) -> str:
        """
        Combine retrieved chunks into a single context string.
        """
        if not results:
            return "No relevant documents found."
            
        context_parts = []
        for i, item in enumerate(results):
            title = item.get("title", f"Document {i+1}")
            desc = item.get("description", "")
            context_parts.append(f"--- Source: {title} ---\n{desc}\n")
            
        return "\n".join(context_parts)

    async def _generate_answer(self, query: str, user_context: str, context_text: str) -> str:
        """
        Calls Gemini LLM to generate the final response.
        """
        prompt = f"""You are an agricultural assistant AI helping farmers.
Use the provided Context Information to answer the User Query.
Ensure the answer is tailored to the Farmer Context if applicable.
If the Context Information does not contain the answer, say "I don't have enough information on that specific topic based on available agricultural schemes." Do not hallucinate schemes.

Farmer Context:
{user_context}

Context Information:
{context_text}

User Query:
{query}

Answer clearly and concisely, focusing on practical advice or steps the farmer can take according to the schemes.
"""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error generating answer: {str(e)}"