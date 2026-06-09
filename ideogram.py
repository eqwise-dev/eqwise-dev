import requests


class IdeogramClient:
    BASE_URL = "https://api.ideogram.ai"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Api-Key": api_key, "Content-Type": "application/json"}

    def generate(
        self,
        prompt: str,
        negative_prompt: str = None,
        model: str = "V_2",
        aspect_ratio: str = "ASPECT_1_1",
        style_type: str = "DESIGN",
        magic_prompt_option: str = "OFF",
        num_images: int = 2,
        seed: int = None,
    ) -> dict:
        payload = {
            "image_request": {
                "prompt": prompt,
                "model": model,
                "aspect_ratio": aspect_ratio,
                "style_type": style_type,
                "magic_prompt_option": magic_prompt_option,
                "num_images": num_images,
            }
        }
        if negative_prompt:
            payload["image_request"]["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["image_request"]["seed"] = seed

        response = requests.post(
            f"{self.BASE_URL}/generate",
            headers=self.headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def upscale(self, image_url: str) -> dict:
        payload = {"image_request": {"image_url": image_url}}
        response = requests.post(
            f"{self.BASE_URL}/upscale",
            headers=self.headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
