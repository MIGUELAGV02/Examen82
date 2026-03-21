from models import db
from datetime import datetime


class Curso(db.Model):
    """Modelo para los cursos"""
    
    __tablename__ = 'cursos'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    categoria = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Curso {self.nombre}>'
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'categoria': self.categoria,
            'categoria_nombre': self.categoria_rel.nombre if self.categoria_rel else None,
            'precio': self.precio,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }
