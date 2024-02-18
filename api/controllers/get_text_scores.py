import textstat
import re
import json

import api.services.adjust_text as adj_txt

def generate_prompt(prompt_bb, paragraph):
    # Extract values from the prompt_parameters dictionary
    text_to_analyze = paragraph
    adjustment_parameters = prompt_bb["adjustment_parameters"]
    ai_target_estimations = prompt_bb["ai_target_estimations"]

    estimated_targets_dict = {"estimated_targets": []}

    for param in adjustment_parameters:
        if param["type"] in ai_target_estimations:
            estimated_targets_dict["estimated_targets"].append({"type": f'{param["type"]}', "target_options": f'{param["targets"]}'})

    estimated_targets_str = json.dumps(estimated_targets_dict, ensure_ascii=False)

    # Extract the prompt for "text_adjusment"
    target_estimation_prompt = next((template["prompt"] for template in prompt_bb["prompt_templates"] if template["type"] == "target_estimation"), None)

    # Fill in the template
    prompt = target_estimation_prompt.format(
        text_to_analyze = text_to_analyze,
        parameters_to_estimate=estimated_targets_str
    )

    return prompt

def get_ai_estimated_targets(prompt_bb, paragraph):

    try:
        prompt = generate_prompt(prompt_bb=prompt_bb, paragraph=paragraph)

        estimated_targets_txt = adj_txt.get_response_from_gemini(prompt)

        print(f"result AI dict:\n{estimated_targets_txt}")

        start_index = estimated_targets_txt.find('{')
        end_index = estimated_targets_txt.rfind('}') + 1
        estimated_targets_txt = estimated_targets_txt[start_index:end_index]

        # Try to parse the extracted JSON object directly
        try:
            result_dict = json.loads(estimated_targets_txt)
            return result_dict
        
        except json.JSONDecodeError:
            # If direct parsing fails, apply preprocessing and try again
            
            # Basic cleanup and replacements
            corrected_str = estimated_targets_txt.strip()
            corrected_str = corrected_str.replace("'", "\"")

            # Ensure spaces after commas for better readability and standard JSON formatting
            corrected_str = re.sub(r',(\S)', r', \1', corrected_str)

            # Add missing commas between objects in arrays, if any
            corrected_str = re.sub(r'\}(?=\s*\{)', r'},', corrected_str)

            # Remove potential trailing commas before closing brackets/braces which JSON does not allow
            corrected_str = re.sub(r',\s*([\]}])', r'\1', corrected_str)

            try:
                dict_str = re.search(r"\{.*?\"estimated_targets\":.*?\}", corrected_str, re.DOTALL).group(0)

                result_dict = json.loads(dict_str)

                return result_dict
            except json.JSONDecodeError as json_err:
                print(f"Failed to parse even after preprocessing: {json_err}")
        
        except AttributeError:
            print("Failed to find a JSON-like structure in the model's output.")
            # You might want to log the output_text or take other actions here.

        except Exception as e:
            print(f"An unexpected error occurred while parsing the model's output: {e}")
            # Handle unexpected errors.

        return None

        # estimated_targets = []
        # lines = estimated_targets_txt.split('\n')
        # for line in lines:
        #     if ':' in line:
        #         param_type, estimated_target = line.split(':', 1)
        #         param_type = param_type.strip()
        #         estimated_target = estimated_target.strip()
        #         estimated_targets.append({"type": param_type, "estimated_target": estimated_target})
        # return {"estimated_targets": estimated_targets}
    
    except Exception as e:
        print(f"Error in get_ai_estimated_targets: {e}")
        raise

def get_classic_estimated_targets(prompt_bb, paragraph):

    targets_dict = {"estimated_targets": []}

    for classic_target in prompt_bb["cllasic_target_estimations"]:

        if classic_target == "Readability":
            readability_score = get_readability_score(text=paragraph, single_score=True)
            targets_dict["estimated_targets"].append({"type": "Readability", "estimated_target": f"{readability_score}"})

        elif classic_target == "Length":
            text_length = get_length_of_text(text=paragraph)
            targets_dict["estimated_targets"].append({"type": "Length", "estimated_target": f"{text_length}"})
    
    return targets_dict

def get_readability_score(text, single_score=False):
    # Calculate various readability scores
    flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
    gunning_fog = textstat.gunning_fog(text)
    smog_index = textstat.smog_index(text)
    coleman_liau_index = textstat.coleman_liau_index(text)

    scores_dict = {
        "flesch_kincaid_grade": flesch_kincaid_grade,
        "gunning_fog_index": gunning_fog,
        "smog_index": smog_index,
        "coleman_liau_index": coleman_liau_index
    }

    if single_score:
        return flesch_kincaid_grade
    else:
        return scores_dict

def get_length_of_text(text):

    text_length = len(text) - 1

    return int(text_length)

if __name__ == "main":

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