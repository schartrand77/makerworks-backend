from fastapi.middleware.cors import CORSMiddleware

def add_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
 	    "http://localhost:5173",
        "https://makerworks.app",
        "https://auth.makerworks.app"
        "http://100.72.184.28:5173"
        
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )