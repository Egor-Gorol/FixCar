from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
import httpx
from routes.auth import get_current_user

templates = Jinja2Templates(directory="templates")
router = APIRouter(include_in_schema=False)


@router.get("/")
async def home(request: Request, error: str | None = None):
    return templates.TemplateResponse("index.html", {"request": request, "error": error})


@router.get("/account")
async def account_dashboard(request: Request, current_user: dict = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
         response = await client.get(
            f"http://localhost:8000/account/user/me",
            headers={"Authorization": f"Bearer {request.cookies.get('access_token')}"}
         )
         user_data = response.json()

    return templates.TemplateResponse("account_dashboard.html", {"request": request, "user_data": user_data})

@router.get("/auth/register")
async def register(request: Request, error: str | None = None):
    return templates.TemplateResponse("registr.html", {"request": request, "error": error})


@router.get("/auth/login")
async def login(request: Request, error: str | None = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@router.get("/requests/new")
async def new_request(request: Request, error: str | None = None):
    return templates.TemplateResponse("request_new.html", {"request": request, "error": error})