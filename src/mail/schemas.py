from pydantic import BaseModel, EmailStr


class EmailValidator(BaseModel):
    address: list[EmailStr]
