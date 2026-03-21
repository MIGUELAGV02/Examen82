from models import db
from werkzeug.security import generate_password_hash, check_password_hash


class Usuario(db.Model):
    """Modelo para usuarios autenticables con JWT"""

    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    correo = db.Column(db.String(120), nullable=False, unique=True)
    contrasena = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str) -> None:
        self.contrasena = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.contrasena, password)

    def to_dict(self):
        return {
            'id': self.id,
            'correo': self.correo,
            'contrasena': self.contrasena
        }
