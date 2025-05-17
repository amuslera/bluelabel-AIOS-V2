from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from Bluelabel AIOS v2"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting simple test API on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)