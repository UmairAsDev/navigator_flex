from route import router
from fastapi import FastAPI

app = FastAPI()


app.include_router(router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Flexport API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000, reload=True)