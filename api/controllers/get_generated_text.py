import api.services.adjust_text as adj_txt

def generate_prompt(prompt_parameters, prompt_template):
    # Extract values from the prompt_parameters dictionary
    entire_text = prompt_parameters.get("entire_text", "")
    text_to_adjust = prompt_parameters.get("text_to_adjust", "")
    adjustments = prompt_parameters.get("user_adjustments", [])
    additional_instructions = prompt_parameters.get("additional_instructions", "Maintain the core narrative and themes of the original text.")

    # Format the adjustments into a list
    adjustments_list = '\n'.join('- {}: {}'.format(adj['type'], adj['target']) for adj in adjustments)

    # Format the types of adjusments into string
    # Generate a list of unique adjustment types from the adjustments
    adjustment_types = {adj['type'] for adj in adjustments}
    # Format the adjustment_types into a comma-separated string
    adjustment_types_str = ", ".join(sorted(adjustment_types))

    # Fill in the template
    prompt = prompt_template.format(
        adjusment_types=adjustment_types_str,
        entire_text=entire_text,
        text_to_adjust=text_to_adjust,
        adjustments_list=adjustments_list,
        additional_instructions=additional_instructions
    )
    
    return prompt

def get_generated_text(prompt_bb):

    prompt_parameters = prompt_bb["prompt_parameters"]
    # Extract the prompt for "text_adjusment"
    text_adjustment_prompt = next((template["prompt"] for template in prompt_bb["prompt_templates"] if template["type"] == "text_adjusment"), None)

    prompt = generate_prompt(prompt_parameters=prompt_parameters, prompt_template=text_adjustment_prompt)

    adjusted_text = adj_txt.get_response_from_gemini(prompt)

    return adjusted_text

if __name__ == "main":

    prompt_template = """
    You are tasked with adjusting a provided text according to specific parameters. Your goal is to modify the specific 'Text to adjust' to meet the designated {adjusment_types}, without losing the essence and thematic elements of the entire original text.\n\nThe Entire Original Text: '{entire_text}'\The Text To Be Adjusted: '{text_to_adjust}'\n\nAdjustments Required:\n{adjustments_list}\n\nAdditional Instructions: {additional_instructions}\n\nPlease rewrite the text provided, applying the adjustments listed above. Ensure that the revised text aligns with the specified parameters while preserving the original's narrative flow and thematic content. The final text should reflect the adjustments in a cohesive and natural manner.
    """

    prompt_parameters = {
        "entire_text": "Under a starlit sky, a solitary figure contemplates the vastness of the cosmos, pondering the mysteries it holds.",
        "text_to_adjust": "",  # Assuming this might be empty and we use the entire text
        "adjustments": [
            {"type": "Readability", "target": "5th Grade Level"},
            {"type": "Tone", "target": "Optimistic"},
            {"type": "Style", "target": "Narrative"},
            {"type": "Vocabulary", "target": "Simplified"},
            {"type": "Emotional Intensity", "target": "Increased"}
        ],
        "additional_instructions": "Maintain the core narrative and themes of the original text."
    }

    prompt_text = generate_prompt(prompt_parameters, prompt_template)
    print(prompt_text)
