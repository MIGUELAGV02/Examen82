from flask import request
from flask_restful import Resource
from models import db
from models.categoria import Categoria

class CategoriaCreateResource(Resource):
    def post(self):
        """Crear una nueva categoría"""
        try:
            data = request.get_json()
            
            # Validaciones
            if not data:
                return {'error': 'No se proporcionaron datos'}, 400
            
            if not data.get('nombre'):
                return {'error': 'El nombre es requerido'}, 400
            
            # Verificar si ya existe
            existing = Categoria.query.filter_by(nombre=data['nombre']).first()
            if existing:
                return {'error': 'Ya existe una categoría con ese nombre'}, 409
            
            # Crear categoría
            nueva_categoria = Categoria(
                nombre=data['nombre'],
                descripcion=data.get('descripcion', '')
            )
            
            db.session.add(nueva_categoria)
            db.session.commit()
            
            return {
                'message': 'Categoría creada exitosamente',
                'categoria': nueva_categoria.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Error al crear la categoría: {str(e)}'}, 500


class CategoriaListResource(Resource):
    def get(self):
        """Listar todas las categorías (auxiliar para referencia)"""
        try:
            categorias = Categoria.query.all()
            return {
                'categorias': [cat.to_dict() for cat in categorias],
                'total': len(categorias)
            }, 200
        except Exception as e:
            return {'error': f'Error al obtener categorías: {str(e)}'}, 500
