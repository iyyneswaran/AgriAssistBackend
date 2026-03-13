from google import genai
from typing import List, Dict, Any
from app.core.config import settings

from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.retriever import Retriever
from app.services.rag.scheme_ranker import SchemeRanker


class RagService:
    """
    Orchestrates RAG pipeline for scheme recommendation.
    Works with a farm_context dict instead of User ORM model.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.retriever = Retriever()
        self.ranker = SchemeRanker()
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

    def build_user_context(self, farm_context: Dict[str, Any]) -> str:
        """
        Build structured context string for embedding from farm context dict.
        """
        parts = []
        if farm_context.get("crop"):
            parts.append(f"Primary crop: {farm_context['crop']}")
        if farm_context.get("soil_type"):
            parts.append(f"Soil type: {farm_context['soil_type']}")
        if farm_context.get("area_acres"):
            parts.append(f"Land size: {farm_context['area_acres']} acres")
        if farm_context.get("state"):
            parts.append(f"State: {farm_context['state']}")
        if farm_context.get("district"):
            parts.append(f"District: {farm_context['district']}")

        return "\n".join(parts) if parts else "Indian farmer seeking agricultural schemes"

    async def recommend_schemes(
        self,
        query: str,
        farm_context: Dict[str, Any],
        top_k: int = 8,
    ) -> Dict[str, Any]:
        """
        Full RAG flow:
        1. Build user context from farm_context dict
        2. Embed query + context
        3. Retrieve similar schemes
        4. Apply ranking/filtering
        5. Generate final answer with LLM using retrieved context
        """

        # 1️⃣ Build contextual query
        user_context = self.build_user_context(farm_context)

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

        # 4️⃣ Post-filtering / ranking using farm context
        ranked_results = self.ranker.rank(results, farm_context)

        # 5️⃣ Generate Final Answer using context
        context_text = self._build_retrieved_context(ranked_results)
        final_answer = await self._generate_answer(query, user_context, context_text)

        return {
            "answer": final_answer,
            "source_documents": ranked_results
        }

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
            eligibility = item.get("eligibility", "")
            benefit = item.get("benefit_amount", "")
            context_parts.append(
                f"--- Scheme: {title} ---\n"
                f"Description: {desc}\n"
                f"Eligibility: {eligibility}\n"
                f"Benefit: {benefit}\n"
            )
            
        return "\n".join(context_parts)

    async def _generate_answer(self, query: str, user_context: str, context_text: str) -> str:
        """
        Calls Gemini LLM to generate the final response.
        """
        prompt = f"""You are an agricultural assistant AI helping Indian farmers find relevant government schemes.
Use the provided Context Information to answer the User Query.
Ensure the answer is tailored to the Farmer Context if applicable.
If the Context Information does not contain the answer, say "I don't have enough information on that specific topic based on available agricultural schemes." Do not hallucinate schemes.

Farmer Context:
{user_context}

Context Information:
{context_text}

User Query:
{query}

Provide a concise summary of relevant schemes available for this farmer. Focus on:
1. Which schemes match the farmer's crop, region, and farm size
2. Key benefits and eligibility criteria
3. Any specific steps the farmer should take to avail these schemes
"""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error generating answer: {str(e)}"