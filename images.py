from openai import OpenAI

class ImageGenerator:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client

    def generate(self, prompt):
        try:
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024",
                response_format="b64_json",
                quality="standard",
            )
            image_data = response.data[0]
            return {
                "b64_json": image_data.b64_json,
                "prompt": image_data.revised_prompt
            }
        except Exception as e:
            return {"error": str(e)}

