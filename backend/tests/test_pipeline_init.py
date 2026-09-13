from app.services.processor.pipeline import ProcessorPipeline
from app.api.processor import ProcessPayload
import os

def test_pipeline():
    pipeline = ProcessorPipeline()
    config = ProcessPayload(video_url="test") # Fake config
    # We can't really run process_video without a real video path because it checks os.path.exists
    print("Pipeline initialized successfully.")

if __name__ == "__main__":
    test_pipeline()
