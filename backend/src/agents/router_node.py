from langchain_ollama.chat_models import ChatOllama
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import json
import re

ollama_model = ChatOllama(model="gemma:2b")

# ---------- Schema ----------
class RelevantData(BaseModel):
    order_id: str | None = Field(None)
    product_id: str | None = Field(None)
    name: str | None = Field(None)
    brand: str | None = Field(None)
    colour: str | None = Field(None)
    fabric: str | None = Field(None)
    occasion: str | None = Field(None)
    print_pattern: str | None = Field(None)
    top_type: str | None = Field(None)
    sleeve_length: str | None = Field(None)
    description: str | None = Field(None)

parser = PydanticOutputParser(pydantic_object=RelevantData)

def router_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Router determines intent + extracts relevant data fields.
    Also merges with previous relevant data for context persistence.
    """
    user_input = state.get("latest_input", "").strip()
    if not user_input:
        return {"intent": "none"}

    prev_relevant_data = state.get("relevant_data", {})
    extracted_data = {} # Will hold {'intent': '...', 'relevant_data': {...}}
    
    print(f"🧩 Incoming relevant_data: {prev_relevant_data}")

    # ... (routing_prompt preparation remains the same)

    routing_prompt = f"""
    Conversation so far:
    {state.get("messages", [])[-4:]}

    User said: "{user_input}"

    Step 1: Determine intent
    - "details" if asking for product/order info shipping details product image etc or any information to be extracted from sql
    - "billing" if asking to buy or payment after recommendation
    - "recommendation" if asking for similar products or suggestions
    - "none" otherwise

    Step 2: You are a structured information extractor.
    The user might mention order IDs, product IDs, or describe products.
    Return relevant data as JSON following this schema:
    {parser.get_format_instructions()}

    Examples:
    - "what is my order 12" → {{ "order_id": "12" }}
    - "show product id 1020" → {{ "product_id": "1020" }}
    - "find blue kurta by W" → {{ "colour": "blue", "brand": "W" }}
    - "for order of id 9" → {{ "order_id": "9" }}

    Message: "{user_input}"

    Example output:
    {{
      "intent": "details",
      "relevant_data": {{
          "order_id": "1234",
          "product_id": null,
          "description": "red printed kurta"
      }}
    }}
    """

    llm_response = ollama_model.invoke(routing_prompt)
    
    try:
        # 1. Robustly parse the entire JSON object from the LLM
        full_output = json.loads(llm_response.content) 
        
        # 2. Extract intent
        intent = full_output.get("intent", "none")
        
        # 3. Parse relevant_data using Pydantic
        relevant_data_content = full_output.get("relevant_data", {})
        parsed_relevant_data = parser.parse_obj(relevant_data_content)
        
        extracted_data = {
            "intent": intent,
            "relevant_data": parsed_relevant_data.dict(exclude_none=True)
        }
        print("✅ Pydantic Data Parsing Successful.")
        
    except Exception as e:
        # --- DATA EXTRACTION FALLBACK (CRITICAL FIX) ---
        print(f"❌ Pydantic Data Parsing failed: {e}. Falling back to Context/Regex...")
        
        # 1. Start the new extracted data as a copy of the previous state (Context Persistence Guarantee)
        newly_extracted_data_for_merge = dict(prev_relevant_data)
        
        # 2. Add basic regex for NEW IDs (will overwrite old IDs if new ones are explicitly stated)
        user_input_lower = user_input.lower()
        if order_match := re.search(r"\b(?:order|id)\s*(\d+)\b", user_input_lower):
            newly_extracted_data_for_merge["order_id"] = order_match.group(1)
            print(f"▶️ Regex found new order_id: {order_match.group(1)}")
        if product_match := re.search(r"\b(?:product|item)\s*(?:id|number)?\s*(\d+)\b", user_input_lower):
             newly_extracted_data_for_merge["product_id"] = product_match.group(1)
             print(f"▶️ Regex found new product_id: {product_match.group(1)}")
        
        # 3. CRITICAL: Determine Intent based on available data
        if newly_extracted_data_for_merge:
             # If we have any data (new ID or persistent old context), we assume the intent is 'details'
             intent = "details" 
        else:
             # If no data and parsing failed, we default to 'none'
             intent = "none"

        extracted_data = {
            "intent": intent,
            "relevant_data": newly_extracted_data_for_merge
        }


    state["intent"] = extracted_data["intent"]

    # --- FINAL STATE MERGE ---
    # We start from the incoming state (prev_relevant_data)
    merged_data = dict(prev_relevant_data)

    # We merge in the data from the extraction (which is either fresh or the full previous state)
    for key, val in extracted_data['relevant_data'].items():
        # If a new value exists (non-empty), add/overwrite it
        if val is not None and str(val).strip() != "":
            merged_data[key] = val

    # Save back into state
    state["relevant_data"] = merged_data

    print("Extracted_data is here" , {"intent": state["intent"], "relevant_data": extracted_data['relevant_data']})
    print(f"🧩 Merged relevant_data: {merged_data}")

    print(f"🧭 Intent: {state['intent']}")
    print(f"🧩 Relevant Data: {merged_data}")
    return state