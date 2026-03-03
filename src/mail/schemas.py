from pydantic import BaseModel, EmailStr


class EmailValidator(BaseModel):
    addresses: list[EmailStr]
