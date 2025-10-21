from langchain_ollama.chat_models import ChatOllama
from typing import Dict, Any, List
from src.agents.sql_node import sql_node 
import json
import re

ollama_model = ChatOllama(model="gemma:2b")
MAX_RECS = 3 # Fetch up to 3 recommendations

def recommendation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates product recommendations based on existing order context or user's explicit query.
    It uses the LLM to formulate a relevant search query/keywords for the SQL node.
    """
    user_input = state.get("latest_input", "").strip()
    relevant_data = state.get("relevant_data", {})
    
    # --- 1. Determine Search Strategy (LLM Prompt for Keywords) ---

    context_desc = (
        relevant_data.get('description') or 
        relevant_data.get('name') or 
        relevant_data.get('brand')
    )
    
    context_prompt = f"The user's previous context item is: '{context_desc}'. " if context_desc else ""

    search_prompt = f"""
    The user asked for recommendations: "{user_input}"
    {context_prompt}

    Your goal is to extract the absolute best 3-5 distinct keywords or product attributes (color, style, fabric, occasion, etc.) 
    that should be used to search the product database for recommendations. Prioritize attributes explicitly mentioned 
    by the user or derived from the context item's description.

    Return ONLY a single JSON object with a list of strings for the 'keywords' field. 
    Keywords should be distinct, relevant single words or short phrases suitable for a database full-text search.

    Example: User: "show me something good in black"
    Output: {{"keywords": ["black", "topwear"]}}
    """
    
    keywords = []
    try:
        llm_response = ollama_model.invoke(search_prompt)
        json_content = json.loads(llm_response.content.strip())
        keywords = [str(k).strip() for k in json_content.get("keywords", []) if str(k).strip()]
        
        if not keywords:
            raise ValueError("LLM failed to return valid keywords.")
            
    except Exception:
        # Fallback to simple tokenization of user input if LLM fails
        keywords = re.findall(r'\b\w{3,}\b', user_input.lower()) 
        # Simple stopwords cleanup
        stopwords = ['show', 'me', 'product', 'similar', 'good', 'something', 'ordered', 'want', 'to', 'buy', 'by']
        keywords = [k for k in keywords if k not in stopwords]
        
        if not keywords:
            state["error_msg"] = "Could not generate effective search terms for recommendation."
            return state

    # --- 2. Execute SQL Search ---
    
    # Pass keywords to the SQL node via a temporary data structure
    temp_relevant_data = dict(relevant_data)
    temp_relevant_data['search_keywords'] = keywords
    
    # Call the SQL node in recommendation mode
    recommendation_result = sql_node(temp_relevant_data, state.get("user_id"), mode='recommendation', limit=MAX_RECS)
    
    if "error" in recommendation_result:
        state["error_msg"] = recommendation_result["error"]
        return state

    # --- 3. Generate Final Response ---
    
    recs_list = recommendation_result.get('recommendations', [])
    if not recs_list:
        state["error_msg"] = "We couldn't find any products matching your criteria."
        return state

    # Prepare list of recommended items for LLM response generation
    recs_summary = "\n".join([
        f"- {item['NAME']} by {item['BRAND']} (ID: {item['P_ID']}): {item['DESCRIPTION'][:50]}... Price: {item['PRICE']}"
        for item in recs_list
    ])

    final_prompt = f"""
    The user asked for recommendations based on the query: "{user_input}".
    The following {len(recs_list)} products were found:
    {recs_summary}

    Generate a polite, engaging response presenting the recommendations.
    - Mention the name, brand, and a brief description/price for each product.
    - Inform the user that they can ask for 'details' or 'image' using the Product ID (P_ID).
    - Do not show the raw SQL data.
    """

    llm_response = ollama_model.invoke(final_prompt)
    
    # Update state
    state["messages"].append({"role": "reco_agent", "content": llm_response.content})
    state["error_msg"] = None
    
    return state