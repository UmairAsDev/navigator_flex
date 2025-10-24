from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from route import router

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Flexport API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000, reload=True)
