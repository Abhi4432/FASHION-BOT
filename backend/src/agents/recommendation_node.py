from langchain_ollama.chat_models import ChatOllama
from typing import Dict, Any, List
from src.agents.sql_node import sql_node 
import json
import re

ollama_model = ChatOllama(model="gemma:2b")
MAX_RECS = 1 # Fetch up to 3 recommendations

def recommendation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates product recommendations based on existing order context or user's explicit query.
    It uses the LLM to formulate a relevant search query/keywords for the SQL node.
    """
    user_input = state.get("latest_input", "").strip()
    relevant_data = state.get("relevant_data", {})
    
    # --- 1. Get Keywords (Filter and prepare FTS search terms) ---

    # Define the only fields relevant for Full-Text Search (FTS) in PRODUCTS table
    PRODUCT_FTS_KEYS = [
        'name', 'brand', 'colour', 'fabric', 'occasion', 
        'print_pattern', 'top_type', 'sleeve_length', 'description'
    ]
    
    # Extract FTS attributes from relevant_data and ensure they are strings
    search_keywords = [
        str(v) 
        for k, v in relevant_data.items() 
        if k in PRODUCT_FTS_KEYS and v is not None and str(v).strip() != ""
    ]
    
    # Fallback/refinement logic for keywords if only raw text is available
    if not search_keywords:
        context_desc = relevant_data.get('description') or relevant_data.get('name')
        
        search_prompt = f"""
        The user asked for recommendations: "{user_input}"
        Context: {context_desc or 'None'}
        
        Task: Extract the 3-5 best keywords (color, style, fabric, etc.) for a full-text search.
        Return ONLY a single JSON object with a list of strings for the 'keywords' field.
        """
        
        try:
            llm_response = ollama_model.invoke(search_prompt)
            json_content = json.loads(llm_response.content.strip())
            # Ensure LLM-generated keywords are explicitly strings
            search_keywords = [str(k).strip() for k in json_content.get("keywords", []) if str(k).strip()]
        except Exception:
            # Simple tokenization fallback
            keywords_temp = re.findall(r'\b\w{3,}\b', user_input.lower()) 
            stopwords = ['show', 'me', 'product', 'similar', 'good', 'something', 'ordered', 'want', 'to', 'buy', 'by']
            search_keywords = [k for k in keywords_temp if k not in stopwords]
            
    if not search_keywords:
        state["error_msg"] = "No valid search terms were identified for product recommendation."
        return state

    # --- 2. Execute SQL Search ---
    
    # Pass keywords to the SQL node via a temporary data structure
    temp_relevant_data = dict(relevant_data)
    temp_relevant_data['search_keywords'] = search_keywords # Keywords are now guaranteed to be strings
    
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
    - If image is available then provide the image URL.
    - Do not show the raw SQL data.
    """

    llm_response = ollama_model.invoke(final_prompt)
    
    # Update state
    state["messages"].append({"role": "reco_agent", "content": llm_response.content})
    state["error_msg"] = None
    
    return state