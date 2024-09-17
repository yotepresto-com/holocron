from fastapi import FastAPI
from app.routers import user, role, profile, product, risk, blacklist, transaction

app = FastAPI()

app.include_router(user.router)
app.include_router(role.router)
app.include_router(profile.router)
app.include_router(product.router)
app.include_router(risk.router)
app.include_router(blacklist.router)
app.include_router(transaction.router)

# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker