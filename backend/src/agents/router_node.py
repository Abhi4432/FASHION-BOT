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
    user_input = state.get("latest_input", "").strip()
    if not user_input:
        return {"intent": "none"}

    prev_relevant_data = state.get("relevant_data", {})
    
    # Text summary of previous context to help the LLM prioritize
    context_summary = "\n".join([f"{k}: {v}" for k, v in prev_relevant_data.items() if k not in ['type', 'user_id', 'img']])

    routing_prompt = f"""
    Previous Context (Product or Order Info):
    ---
    {context_summary or "No previous order/product context found."}
    ---

    User's New Query: "{user_input}"

    Step 1: Determine the INTENT based **ONLY on the User's New Query**.
    
    INTENT RULES:
    1. **"details"**: Select this if the user is asking about an **EXISTING entity**.
       - Examples: "What is the status of order 1?", "Show me the price of product 19135002.", "What is the delivery date?", "Show me the image for the red dress."
       - **Crucial:** Even if the context is present, if the user asks a question like "What is the status?", the intent is still "details" for retrieval.

    2. **"recommendation"**: Select this if the user is asking for **NEW, SIMILAR, or suggested products**.
       - Examples: "Show some kurti in red", "Find products similar to what I ordered.", "What's good in black?", "Show me a formal shirt."
       - **Crucial:** Queries that specify new product attributes (like "red" or "kurti") that require a database search for NEW items must be "recommendation."

    3. **"none"**: For greetings, farewells, or irrelevant topics.

    Step 2: Extract Relevant Data
    - Extract any product attributes mentioned in the User's New Query (e.g., colour, top_type).
    - If the user explicitly mentions an `order_id` or `product_id`, extract that as well.

    Return ONLY a single JSON object.
    
    Example 1 (Recommendation):
    User Query: "can you show some kurti in red"
    Output:
    {{
      "intent": "recommendation",
      "relevant_data": {{
          "colour": "Red",
          "top_type": "kurti"
      }}
    }}

    Example 2 (Details):
    User Query: "what is the shipping date for order 1"
    Output:
    {{
      "intent": "details",
      "relevant_data": {{
          "order_id": "1"
      }}
    }}
    """

    llm_response = ollama_model.invoke(routing_prompt)
    extracted_data = {}
    
    try:
        # 1. Robustly parse the entire JSON object from the LLM
        full_output = json.loads(llm_response.content.strip())
        intent = full_output.get("intent", "none")
        relevant_data_content = full_output.get("relevant_data", {})
        
        # 2. Validate data structure and filter None/empty strings
        parsed_relevant_data = parser.parse_obj(relevant_data_content)
        
        extracted_data = {
            "intent": intent,
            "relevant_data": parsed_relevant_data.dict(exclude_none=True)
        }
        
    except Exception as e:
        # --- DATA EXTRACTION FALLBACK (CRITICAL FIX) ---
        print(f"❌ Pydantic Data Parsing failed: {e}. Falling back to Context/Regex...")
        
        newly_extracted_data_for_merge = dict(prev_relevant_data)
        
        user_input_lower = user_input.lower()
        if order_match := re.search(r"\b(?:order|id)\s*(\d+)\b", user_input_lower):
            newly_extracted_data_for_merge["order_id"] = order_match.group(1)
            
        # Fallback Intent Logic (Prioritizes Recommendation)
        if any(w in user_input_lower for w in ['similar', 'recommend', 'show me', 'find me', 'kurti', 'dress', 'shirt', 'good in']):
            intent = "recommendation"
        elif newly_extracted_data_for_merge.get('order_id') or newly_extracted_data_for_merge.get('product_id'):
            # If an ID is present but no clear recommendation keywords, assume details
            intent = "details"
        else:
            intent = "none"

        extracted_data = {
            "intent": intent,
            "relevant_data": newly_extracted_data_for_merge
        }


    print(f"Extracted_data is here {extracted_data}")

    state["intent"] = extracted_data.get("intent", "none")

    # Combine previously stored relevant data with new extraction
    merged_data = dict(prev_relevant_data)

    for key, val in extracted_data['relevant_data'].items():
        # Only overwrite if the new value is explicitly set and not empty
        if val is not None and str(val).strip() != "":
            merged_data[key] = val
        # CRITICAL: Do not delete existing context fields unless overwritten by the user

    state["relevant_data"] = merged_data
    
    return state