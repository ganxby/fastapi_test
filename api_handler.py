from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Security,
    status
)

from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from database import engine, SessionLocal

from passlib.context import CryptContext
import jwt

import models
import crud
import schema


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


app = FastAPI()

models.Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    """ Return true or false when checking a non hashed password and a hashed password """
    return pwd_context.verify(plain_password, hashed_password)


def auth_user(db: Session, login: str, password: str):
    """ Return true or false when trying to authorize a user """
    user = crud.get_user_by_login(db, login)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False

    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """ Return access token """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """ Return `user` if the input is valid """
    authenticate_value = f"Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            crud.add_log(db, f'[1] Attempt to use invalid authorization data: {username}', datetime.utcnow())
            raise credentials_exception
        token_data = schema.TokenData(login=username)

    except:
        crud.add_log(db, f'[2] Attempt to use invalid authorization data', datetime.utcnow())
        raise credentials_exception

    user = crud.get_user_by_login(db, token_data.login)
    if user is None:
        crud.add_log(db, f'[3] Attempt to use invalid authorization data: {user}', datetime.utcnow())
        raise credentials_exception

    return user


async def get_current_active_user(current_user: schema.User = Security(get_current_user)):
    return current_user


@app.post('/add_user')
async def create_user(user: schema.User, db: Session = Depends(get_db)):
    """ Endpoint to add new user """
    check_user = crud.get_user_by_login(db, login=user.login)
    if check_user:
        crud.add_log(db, f'Attempt to register an existing login `{user.login}`', datetime.utcnow())
        raise HTTPException(status_code=400, detail='Login already registered')

    crud.add_log(db, f'Registration of a new user `{user.login}`', datetime.utcnow())
    return crud.add_user(db=db, user=user)


@app.post("/get_token", response_model=schema.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    """ Endpoint to get new access token """
    user = auth_user(db, form_data.username, form_data.password)
    if not user:
        crud.add_log(db, '[4] Attempt to enter invalid authorization data', datetime.utcnow())
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.login},
        expires_delta=access_token_expires,
    )

    crud.add_log(db, f'Get new token for user `{user.login}`', datetime.utcnow())
    return {"access_token": access_token, "token_type": "Bearer"}


@app.post('/storage/add_product')
async def add_product(product: schema.Product, db: Session = Depends(get_db),
                      current_user: schema.User = Depends(get_current_active_user)):
    """ Endpoint for adding a new product by the seller """
    if current_user.position != 'trader':
        crud.add_log(db, f'Buyer `{current_user.login}` attempting to access trader`s API', datetime.utcnow())
        raise HTTPException(status_code=403, detail='Forbidden')

    crud.add_log(db, f'User `{current_user.login}` added a new product', datetime.utcnow())
    return crud.add_product(db, product)


@app.get('/storage/buy_product')
async def buy_product(current_user: schema.User = Depends(get_current_active_user),
                      db: Session = Depends(get_db)):
    """ Endpoint for the purchase of one unit of goods by the buyer """
    if current_user.position != 'buyer':
        crud.add_log(db, f'Trader `{current_user.login}` attempting to access buyer`s API', datetime.utcnow())
        raise HTTPException(status_code=403, detail='Forbidden')

    crud.add_log(db, f'User `{current_user.login}` bought a product', datetime.utcnow())
    return crud.delete_product(db)
