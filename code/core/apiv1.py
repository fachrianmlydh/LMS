from ninja import NinjaAPI, Schema
from ninja.errors import HttpError
from pydantic import field_validator
import re
from .models import User, CourseMember, CourseContent, Comment, Course
from typing import List

apiv1 = NinjaAPI()

@apiv1.get('/hello')
def helloApi(request):
    return "Menyala abangkuh ..."

@apiv1.get('calc/{nil1}/{opr}/{nil2}')
def calculator(request, nil1: int, opr: str, nil2: int):
    hasil = nil1 + nil2
    if opr == '-':
        hasil = nil1 - nil2
    elif opr == 'x':
        hasil = nil1 * nil2

    return {'nilai1': nil1, 'nilai2': nil2, 'operator': opr, 'hasil': hasil}

@apiv1.post('hello/')
def helloPost(request):
    if 'nama' in request.POST:
        return f"Selamat menikmati ya {request.POST['nama']}"
    return "Selamat tinggal dan pergi lagi"

@apiv1.put('users/{id}')
def userUpdate(request, id: int):
    return f"User dengan id {id} Nama aslinya adalah Herdiono kemudian diganti menjadi {request.body}"

@apiv1.delete('users/{id}')
def userDelete(request, id: int):
    return f"Hapus user dengan id: {id}"

class Kalkulator(Schema):
    nil1: int
    nil2: int
    opr: str
    hasil: int = 0

    def calcHasil(self):
        hasil = self.nil1 + self.nil2
        if self.opr == '-':
            hasil = self.nil1 - self.nil2
        elif self.opr == 'x':
            hasil = self.nil1 * self.nil2

        return {'nilai1': self.nil1, 'nilai2': self.nil2,
                'operator': self.opr, 'hasil': self.hasil}

@apiv1.post('calc')
def postCalc(request, skim: Kalkulator):
    skim.hasil = skim.calcHasil()
    return skim

class Register(Schema):
    username: str
    password: str
    email: str
    first_name: str
    last_name: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value):
        if len(value) < 5:
            raise ValueError("Username minimal 5 karakter")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password minimal 8 karakter")
        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d).+$", value):
            raise ValueError("Password harus mengandung huruf dan angka")
        return value

class UserOut(Schema):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str

@apiv1.post('register/', response=UserOut)
def register(request, data: Register):
    """Registrasi: username min 5 karakter, password min 8 karakter (huruf + angka)."""
    if User.objects.filter(username=data.username).exists():
        raise HttpError(409, "Username sudah dipakai")
    return User.objects.create_user(
        username=data.username, password=data.password, email=data.email,
        first_name=data.first_name, last_name=data.last_name)

class UserSchema(Schema):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str

@apiv1.get("/users", response=List[UserSchema])
def list_users(request):
    users = User.objects.all()
    return users