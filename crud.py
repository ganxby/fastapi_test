from sqlalchemy import desc
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from fastapi import HTTPException

import models
import schema


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user_by_login(db: Session, login: str):
    return db.query(models.User).filter(models.User.login == login).first()


def add_user(db: Session, user: schema.User):
    login = user.login
    hashed_password = get_password_hash(user.password)
    position = user.position
    user_data = models.User(login=login, password=hashed_password, position=position)
    db.add(user_data)
    db.commit()
    db.refresh(user_data)

    return {'status': 200,
            'message': 'User successfully registered'}


def add_product(db: Session, product: schema.Product):
    name = product.name
    product_data = models.Storage(name=name)
    db.add(product_data)
    db.commit()
    db.refresh(product_data)

    return {'status': 200,
            'message': f'Product `{name}` has been added'}


def delete_product(db: Session):
    obj = db.query(models.Storage).order_by(desc(models.Storage.id)).first()

    try:
        db.delete(obj)
    except:
        raise HTTPException(status_code=404, detail='Products not found')

    db.commit()

    return {'status': 200,
            'message': 'The item has been sold'}


def add_log(db: Session, log_event, time_now):
    log_data = models.LogBase(event=log_event, timestamp=time_now)
    db.add(log_data)
    db.commit()
    db.refresh(log_data)
