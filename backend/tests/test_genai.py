
import os, time
def generate_video_gemini(api_key, prompt, image_path=None):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    
    config_args = {
        'aspect_ratio': '16:9',
        'person_generation': 'ALLOW_ADULT'
    }
    
    kwargs = {
        'model': 'veo-2.0-generate-001',
        'prompt': prompt,
        'config': types.GenerateVideosConfig(**config_args)
    }
    
    if image_path and os.path.exists(image_path):
        # We need to upload the image or pass it as bytes
        with open(image_path, 'rb') as f:
            img_bytes = f.read()
        kwargs['image'] = types.Image(image_bytes=img_bytes, mime_type='image/png')
        
    print('Sending request to Veo...')
    operation = client.models.generate_videos(**kwargs)
    print(f'Operation name: {operation.name}')
    
    while not operation.done:
        print('Polling...')
        time.sleep(10)
        # Note: how to poll? We might need to use client.models.get_operation(operation.name) or similar
        # But wait, generate_videos might be synchronous if it waits for result? 
        # Actually Google GenAI SDK returns an Operation object which we can poll.
        # operation.result() might wait for it! Let's check dir(operation)
        break
    return operation.name

