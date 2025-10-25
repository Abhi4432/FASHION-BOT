from langchain_ollama.chat_models import ChatOllama
from typing import Dict, Any, List
from src.agents.sql_node import sql_node 
import json
import re

ollama_model = ChatOllama(model="gemma:2b")
MAX_RECS = 1 # Only fetch 1 recommendation

def recommendation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    user_input = state.get("latest_input", "").strip()
    relevant_data = state.get("relevant_data", {})
    
    # --- 1. Get Keywords ---
    PRODUCT_FTS_KEYS = [
        'name', 'brand', 'colour', 'fabric', 'occasion', 
        'print_pattern', 'top_type', 'sleeve_length', 'description'
    ]
    
    search_keywords = [
        str(v) 
        for k, v in relevant_data.items() 
        if k in PRODUCT_FTS_KEYS and v is not None and str(v).strip() != ""
    ]
    
    keyword_source = "ROUTER_EXTRACTION"
    
    if not search_keywords:
        # Fallback: Use LLM/Regex to extract keywords
        #context_desc = relevant_data.get('description') or relevant_data.get('name')
        context_desc = ", ".join(
            filter(None, [relevant_data.get('colour'), relevant_data.get('brand'), relevant_data.get('name') , relevant_data.get('fabric'), relevant_data.get('print_pattern'), relevant_data.get('top_type'), relevant_data.get('sleeve_length')])
        )
        print(f"DEBUG: Context Description for Keyword Extraction: {context_desc}")
        search_prompt = f"""
        The user asked for recommendations: "{user_input}"
        Context: {context_desc or 'None'}el
        Task: Extract the 3 best keywords (color, style, fabric, etc.) for a full-text search.
        Return ONLY a single JSON object with a list of strings for the 'keywords' field.
        Give preference to user input terms, but supplement with context if needed.So for colour and other attributes use user given input more.
        """
        
        try:
            llm_response = ollama_model.invoke(search_prompt)
            json_content = json.loads(llm_response.content.strip())
            search_keywords = [str(k).strip() for k in json_content.get("keywords", []) if str(k).strip()]
            keyword_source = "LLM_EXTRACTION"
        except Exception:
            # Simple tokenization fallback
            keywords_temp = re.findall(r'\b\w{3,}\b', user_input.lower()) 
            stopwords = ['show', 'me', 'product', 'similar', 'good', 'something', 'ordered', 'want', 'to', 'buy', 'by', 'new', 'kurti', 'in', 'of']
            search_keywords = [k for k in keywords_temp if k not in stopwords]
            keyword_source = "REGEX_FALLBACK"

    # DEBUG STATEMENT: Print keyword source and keywords
    print(f"DEBUG: Recommendation Keywords ({keyword_source}): {search_keywords}")
        
    if not search_keywords:
        state["error_msg"] = "No valid search terms were identified for product recommendation."
        return state
        
    # --- 2. Execute SQL Search ---
    
    temp_relevant_data = dict(relevant_data)
    temp_relevant_data['search_keywords'] = search_keywords 
    
    recommendation_result = sql_node(temp_relevant_data, state.get("user_id"), mode='recommendation', limit=MAX_RECS) 
    
    if "error" in recommendation_result:
        state["error_msg"] = recommendation_result["error"]
        return state

    # --- 3. Merge SQL Data and Final Response ---
    
    recs_list = recommendation_result.get('recommendations', [])
    if not recs_list:
        state["error_msg"] = "We couldn't find any products matching your criteria."
        return state

    recommended_product_data = recs_list[0]
    
    # CRITICAL UPDATE: Override all previous relevant_data with the new product details
    # Clear old keys including lowercase 'img'
    keys_to_clear = ['order_id', 'product_id', 'img'] 
    
    merged_data = {
        k: v for k, v in relevant_data.items() 
        if k not in keys_to_clear and k != 'search_keywords'
    }
    
    # Add new product data. 
    for k, v in recommended_product_data.items():
        if k == 'P_ID':
            merged_data['product_id'] = v
        # CRITICAL: Map the SQL result key 'IMG' to the expected lowercase 'img' key
        elif k == 'IMG':
            merged_data['img'] = v
        else:
             merged_data[k.lower()] = v # e.g. NAME -> name

    # Save the updated, focused product data back to state
    state["relevant_data"] = merged_data 

    print(f"DEBUG: Updated relevant_data in recommendation_node: {state['relevant_data']}")

    # Prepare summary for LLM (using lowercase keys for consistency)
    #product_summary = f"- {recommended_product_data.get('name', 'N/A')} by {recommended_product_data.get('brand', 'N/A')} (ID: {recommended_product_data.get('P_ID', 'N/A')}): {recommended_product_data.get('description', '')[:50]}... Price: {recommended_product_data.get('price', 'N/A')}"

    final_prompt = f"""
    The user asked for a recommendation based on the query: "{user_input}".
    The following product was found:
    {merged_data}

    Generate a polite, engaging response presenting this single recommendation.
    - Mention the name, brand, price and a brief description.
    -Mention the image as well and provide url of the image which is there in provided information.
    -Explicity must provide url of image if available from the product data provided.
    -Ask user if he wants to buy this product.
    - Do not show the raw SQL data summary.
    """

    llm_response = ollama_model.invoke(final_prompt)
    
    state["messages"].append({"role": "reco_agent", "content": llm_response.content})
    state["error_msg"] = None
    
    return state



