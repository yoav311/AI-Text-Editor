import api.services.generate_image as gen_img


def generate_prompt(prompt_parameters, prompt_template, text_version="Old"):
    # Extract values from the prompt_parameters dictionary
    if text_version == "Old":
        input_text = prompt_parameters.get("text_to_adjust", "")
    elif text_version == "New":
        input_text = prompt_parameters.get("adjusted_text", "")
    else:
        raise TypeError(f"the text_version argument must be 'Old' or 'New', but got {text_version} insted")

    # Fill in the template
    prompt = prompt_template.format(scene_text=input_text)
    
    return prompt

def get_generated_image(prompt_bb, text_version="Old"):

    # Extract the prompt for "image_generator"
    image_generation_prompt = next((template["prompt"] for template in prompt_bb["prompt_templates"] if template["type"] == "image_generator"), None)

    prompt_parameters = prompt_bb["prompt_parameters"]

    prompt = generate_prompt(prompt_parameters=prompt_parameters, prompt_template=image_generation_prompt, text_version=text_version)

    image = gen_img.generate_image(prompt)

    return image