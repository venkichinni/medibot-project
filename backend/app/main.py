from fastapi import FastAPI, HTTPException  # FastAPI creates APIs; HTTPException returns proper error responses
from fastapi.middleware.cors import CORSMiddleware  # Allows frontend localhost to call backend API

from app.auth import authenticate_user  # Login helper that checks demo username/password
from app.rbac import get_collections_for_role  # RBAC helper that returns allowed collections for a role
from app.schemas import LoginRequest, ChatRequest  # Request body models for /login and /chat
from app.rag import answer_question  # Qdrant RAG with RBAC filtering
from app.sql_rag import answer_sql_question  # SQL RAG for billing/admin database questions


app = FastAPI(title="MediBot API")  # Create the FastAPI app instance


# Allows the Next.js frontend running on localhost:3000 to call this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """
    Health check endpoint.
    Used to confirm that the backend server is running.
    """
    return {
        "status": "ok",
        "message": "MediBot backend is running",
    }


@app.post("/login")
def login(request: LoginRequest):
    """
    Login endpoint.
    Validates demo credentials and returns the user role plus a demo token.
    """
    user = authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return user


@app.get("/collections/{role}")
def collections(role: str):
    """
    Collections endpoint.
    Returns the document collections accessible to a specific role.
    """
    allowed_collections = get_collections_for_role(role)

    if not allowed_collections:
        raise HTTPException(status_code=404, detail="Unknown role")

    return {
        "role": role,
        "collections": allowed_collections,
    }


def looks_like_sql_question(question: str) -> bool:
    """
    Simple router helper.
    If a question sounds like billing/database analytics, route it to SQL RAG.
    """

    sql_keywords = [
        "claim",
        "claims",
        "amount",
        "revenue",
        "status",
        "billing",
        "patient count",
        "total",
        "average",
        "sum",
        "database",
        "how many",
        "count",
    ]

    question_lower = question.lower()

    return any(keyword in question_lower for keyword in sql_keywords)


@app.post("/chat")
def chat(request: ChatRequest):
    """
    Chat endpoint.
    Routes billing/database questions to SQL RAG.
    Routes normal document questions to Qdrant RAG.
    """

    allowed_collections = get_collections_for_role(request.role)

    if not allowed_collections:
        raise HTTPException(status_code=404, detail="Unknown role")

    if looks_like_sql_question(request.question):
        sql_result = answer_sql_question(
            question=request.question,
            role=request.role,
        )

        if sql_result["retrieval_type"] != "sql_blocked":
            return sql_result

    result = answer_question(
        question=request.question,
        role=request.role,
    )

    return result