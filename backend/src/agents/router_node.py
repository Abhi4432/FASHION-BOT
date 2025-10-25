from langchain_ollama.chat_models import ChatOllama
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import json
import re

ollama_model = ChatOllama(model="gemma:2b")

# ---------- Schema for Relevant Data ----------
class RelevantData(BaseModel):
    order_id: str | None = Field(None, description="The ID of an order the user is asking about. It will be numeric. It will be less than 1000")
    product_id: str | None = Field(None, description="The ID of a product the user is asking about or viewing. It will be numeric in nature .It will be more than 10000")
    name: str | None = Field(None)
    brand: str | None = Field(None)
    colour: str | None = Field(None)
    occasion: str | None = Field(None)
    top_type: str | None = Field(None)
    description: str | None = Field(None, description="A general description of the desired product.")

# Pydantic Parser for RelevantData extraction
data_parser = PydanticOutputParser(pydantic_object=RelevantData)


def router_node(state: Dict[str, Any]) -> Dict[str, Any]:
    user_input = state.get("latest_input", "").strip()
    if not user_input:
        return {"intent": "none"}

    prev_relevant_data = state.get("relevant_data", {})
    
    # Text summary of previous context to help the LLM prioritize
    # Exclude search_keywords as they are intermediate data for a recommendation node
    context_summary = "\n".join([f"{k}: {v}" for k, v in prev_relevant_data.items() if k not in ['type', 'img', 'error_msg', 'search_keywords']])

    # ------------------------------------
    # --- STEP 1: Intent Classification (First LLM Call) ---
    # ------------------------------------
    routing_prompt = f"""
    Analyze the user's latest input and previous context to determine their primary intent.

    Previous Context (Relevant Data):
    {context_summary or 'None'}
    
    User's Latest Input: "{user_input}"
    
    Determine the primary intent. Choose only one from the following:
    - "order" if user asks for status, tracking, or details of a specific order.
    - "product" if user wants product details, description, or features of a specific product.
    - "recommendation" if user asks for similar items or suggestions.
    - "none" otherwise.

    IMPORTANT: Return only one word: order, product, recommendation, or none.
    """

    llm_response = ollama_model.invoke(routing_prompt)
    raw_intent = llm_response.content.strip().lower()

    # FIX: Robust post-process to guarantee valid output and map to workflow intents
    if "recommendation" in raw_intent:
        intent = "recommendation"
    elif "order" in raw_intent or "product" in raw_intent:
        intent = "details" # Maps 'order' or 'product' to the workflow's 'details' node (Viewer)
    else:
        intent = "none"

    state["intent"] = intent
    print(f"DEBUG: Intent set to: {intent} (from raw: {raw_intent})")

    # ------------------------------------
    # --- STEP 2: Relevant Data Extraction (Second LLM Call using Pydantic) ---
    # ------------------------------------
    extracted_data_dict = {}
    if intent != "none":
        
        extraction_prompt = f"""
        Extract any relevant data (IDs and product descriptors) from the user's latest input.
        
        Previous Context (Relevant Data):
        {context_summary or 'None'}
        
        User's Latest Input: "{user_input}"
        
        The intent is determined to be '{intent}'. 
        Focus your extraction on fields relevant to this intent.
        Do not extract irrelevant data for fields where you feel no data is present in the user input. Keep them as none. 
        Use the following format for your output:
        
        {data_parser.get_format_instructions()}
        
        Output only the JSON object.
        """
        
        try:
            llm_response_data = ollama_model.invoke(extraction_prompt)
            # Clean up the LLM output to handle markdown 'json' blocks
            print(f"DEBUG: LLM response for data extraction: {llm_response_data.content}")
            json_str = llm_response_data.content.strip()
            if json_str.startswith("```json"):
                json_str = json_str.strip("```json").strip("```").strip()
            
            extracted_data_dict = json.loads(json_str)
            print(f"DEBUG: Extracted data from LLM: {extracted_data_dict}")
            
        except Exception as e:
            # Pydantic extraction failed (e.g., malformed JSON). Continue with regex fallback.
            print(f"ERROR: Pydantic extraction failed: {e}")
            extracted_data_dict = {}
        # Fallback ID extraction using regex for robustness
        user_input_lower = user_input.lower()
        if order_match := re.search(r"\b(?:order|id)\s*(\d+)\b", user_input_lower):
            if 'order_id' not in extracted_data_dict or extracted_data_dict['order_id'] is None:
                extracted_data_dict["order_id"] = order_match.group(1)
        # Regex updated to include '.' for product IDs like '19135002.0'
        if product_match := re.search(r"\b(?:pid|product|item)\s*([a-zA-Z0-9_\.-]+)\b", user_input_lower):
            if 'product_id' not in extracted_data_dict or extracted_data_dict['product_id'] is None:
                extracted_data_dict["product_id"] = product_match.group(1)


    # ------------------------------------
    # --- STEP 3: Merge Context and Cleanup ---
    # ------------------------------------
    merged_data = dict(prev_relevant_data)

    # 1. New extracted data (prioritized from user input) overwrites old context
    for key, val in extracted_data_dict.items():
        if val is not None and str(val).strip() != "":
            merged_data[key] = val
    
    # 2. Context Persistence (IDs)
    # If the new intent is 'details' and the user didn't provide a new ID, keep the old one.
    if state["intent"] == "details":
         if 'order_id' in prev_relevant_data and 'order_id' not in extracted_data_dict:
             merged_data['order_id'] = prev_relevant_data['order_id']
         if 'product_id' in prev_relevant_data and 'product_id' not in extracted_data_dict:
             merged_data['product_id'] = prev_relevant_data['product_id']
             
    # 3. CRITICAL Context Cleanup for new Recommendation search
    if state["intent"] == "recommendation":
        # Define keys that are attributes/filters for search
        PRODUCT_ATTRIBUTES = ['name', 'brand', 'colour', 'fabric', 'occasion', 'print_pattern', 'top_type', 'sleeve_length', 'description']
        
        # Collect all relevant search keywords from the newly merged data
        search_keywords = []
        for key in PRODUCT_ATTRIBUTES:
            if key in merged_data and merged_data[key] is not None and str(merged_data[key]).strip() != "":
                search_keywords.append(str(merged_data[key]))
        
        # Clear all order/detail-specific keys for a fresh recommendation search
        keys_to_clear = ['order_id', 'product_id', 'status', 'delivery_date', 'shipping_date', 'amount', 'type', 'order_date', 'img', 'price'] + PRODUCT_ATTRIBUTES
        for key in keys_to_clear:
            merged_data.pop(key, None)

        # Store the collected keywords for the recommendation node to use
        # If the list is empty, use a generic fallback keyword
        merged_data['search_keywords'] = search_keywords if search_keywords else ["similar product"] 

    state["relevant_data"] = merged_data
    print(f"DEBUG: Final relevant_data: {state['relevant_data']}")
    
    return state