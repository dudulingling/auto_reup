import uvicorn
import logging
if __name__ == "__main__":
    logging.basicConfig(filename="uvicorn_error.log", level=logging.DEBUG)
    uvicorn.run("main:app", host="127.0.0.1", port=8001, log_level="debug")
