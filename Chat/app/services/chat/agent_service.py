import httpx
import logging
from typing import List, Dict, Any
from app.core.config import settings
from app.services.rag.retriever import Retriever
import json

logger = logging.getLogger(__name__)

class AgentService:
    """
    Handles the Sarvam AI Seva agent conversation loop with tool calling.
    """
    def __init__(self):
        self.api_key = settings.SARWAM_API_KEY # Or maybe SARVAM_API_KEY? Need to check config
        # the config says SARWAM_API_KEY, but wait, the user prompt said SARVAM_API_KEY.
        # Let's use the one in settings, which is SARWAM_API_KEY or we can just get from os.environ
        self.model = settings.SARVAM_CHAT_MODEL
        self.url = "https://api.sarvam.ai/v1/chat/completions"
        self.retriever = Retriever()
        self.max_loops = 3

    async def get_market_prices(self, commodity: str, limit: int = 5) -> str:
        """Tool implementation to get market prices from Supabase"""
        from app.integrations.supabase.supabase_store import SupabaseStore
        store = SupabaseStore()
        if not store.client:
            return "Error: Database connection not available."
        try:
            res = store.client.table("agmarknet_market_prices").select("*").ilike("commodity", f"%{commodity}%").limit(limit).execute()
            if not res.data:
                return f"No market data found for commodity {commodity}."
            
            result_str = f"Market data for {commodity}:\n"
            for row in res.data:
                result_str += f"- Date: {row['arrival_date']}, Market: {row['market']}, Min: {row.get('min_price')}, Max: {row.get('max_price')}, Modal: {row.get('modal_price')}\n"
            return result_str
        except Exception as e:
            logger.error(f"Error fetching market prices: {e}")
            return f"Error fetching market prices: {str(e)}"

    async def find_schemes(self, query: str) -> str:
        """Tool implementation to find schemes"""
        from app.services.rag.embedding_service import EmbeddingService
        embed_service = EmbeddingService()
        try:
            # We pass is_query=True for query embedding
            query_vector = await embed_service.embed_text(query, is_query=True)
            results = await self.retriever.store.query_schemes(embedding=query_vector, top_k=3)
            
            if not results:
                return "No matching schemes found."
            
            res_str = "Found Schemes:\n"
            for r in results:
                res_str += f"Title: {r['title']}\nDesc: {r['description'][:200]}...\nEligibility: {r['eligibility']}\n\n"
            return res_str
        except Exception as e:
            logger.error(f"Error in find_schemes: {e}")
            return f"Error finding schemes: {str(e)}"

    async def build_document_checklist(self, scheme_name: str) -> str:
        """Tool implementation to build document checklist"""
        return f"Document Checklist for {scheme_name}:\n1. Aadhar Card\n2. Land Ownership Proof (Patta/Chitta)\n3. Bank Passbook\n4. Passport Size Photos"

    async def draft_grievance(self, issue_description: str, department: str = "Agriculture") -> str:
        """Tool implementation to draft a grievance"""
        return f"To The {department} Department,\n\nSubject: Grievance regarding {issue_description[:50]}...\n\nDear Sir/Madam,\nI am writing to formally report an issue regarding {issue_description}. Please look into this matter urgently.\n\nSincerely,\n[Farmer Name]"

    def _get_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_market_prices",
                    "description": "Fetch agricultural market prices for a given commodity",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "commodity": {"type": "string", "description": "The name of the crop or commodity (e.g. Paddy, Tomato)"}
                        },
                        "required": ["commodity"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_schemes",
                    "description": "Search the knowledge base for government agricultural schemes based on a user's query or profile",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query describing farmer's situation or desired scheme"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "build_document_checklist",
                    "description": "Generate a list of required documents for applying to a specific scheme",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "scheme_name": {"type": "string", "description": "Name of the agricultural scheme"}
                        },
                        "required": ["scheme_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "draft_grievance",
                    "description": "Draft a formal grievance letter based on the user's issue",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issue_description": {"type": "string", "description": "Description of the issue or complaint"},
                            "department": {"type": "string", "description": "Target department (e.g., Agriculture, Revenue)"}
                        },
                        "required": ["issue_description"]
                    }
                }
            }
        ]

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        if name == "get_market_prices":
            return await self.get_market_prices(**arguments)
        elif name == "find_schemes":
            return await self.find_schemes(**arguments)
        elif name == "build_document_checklist":
            return await self.build_document_checklist(**arguments)
        elif name == "draft_grievance":
            return await self.draft_grievance(**arguments)
        else:
            return f"Error: Unknown tool {name}"

    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Executes a conversation turn with Sarvam AI, handling up to `max_loops` tool calls.
        """
        if not self.api_key:
            return {"role": "assistant", "content": "Error: Sarvam API key not configured."}

        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        current_messages = list(messages)
        tools = self._get_tools()

        async with httpx.AsyncClient() as client:
            for _ in range(self.max_loops):
                payload = {
                    "model": self.model,
                    "messages": current_messages,
                    "tools": tools,
                    "temperature": 0.3
                }

                try:
                    resp = await client.post(self.url, json=payload, headers=headers, timeout=30.0)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error(f"Sarvam API error: {e}")
                    return {"role": "assistant", "content": f"Failed to communicate with AI agent: {str(e)}"}

                message = data["choices"][0]["message"]
                current_messages.append(message)

                if "tool_calls" in message and message["tool_calls"]:
                    for tool_call in message["tool_calls"]:
                        fn_name = tool_call["function"]["name"]
                        fn_args = json.loads(tool_call["function"]["arguments"])
                        logger.info(f"Executing tool {fn_name} with args {fn_args}")
                        
                        tool_result = await self.execute_tool(fn_name, fn_args)
                        
                        current_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": fn_name,
                            "content": tool_result
                        })
                    # loop continues to next iteration to let model process tool results
                else:
                    # No more tool calls, return final response
                    return message

            return {"role": "assistant", "content": "Max tool loops reached. " + message.get("content", "")}
