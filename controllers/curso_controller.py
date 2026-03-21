from flask import request
from flask_restful import Resource
from models import db
from models.curso import Curso
from models.categoria import Categoria
from datetime import datetime

class CursoListResource(Resource):
    def get(self):
        """
        Listar todos los cursos con filtros opcionales
        
        Filtros disponibles:
        - categoria: ID de la categoría
        - fecha_inicio: Fecha de inicio del rango (formato: YYYY-MM-DD)
        - fecha_fin: Fecha de fin del rango (formato: YYYY-MM-DD)
        
        Ejemplo: /courses?categoria=1&fecha_inicio=2026-03-20&fecha_fin=2026-03-25
        """
        try:
            # Obtener parámetros de filtro
            categoria_id = request.args.get('categoria', type=int)
            fecha_inicio = request.args.get('fecha_inicio', type=str)
            fecha_fin = request.args.get('fecha_fin', type=str)
            
            # Query base
            query = Curso.query
            
            # Filtrar por categoría
            if categoria_id:
                query = query.filter(Curso.categoria == categoria_id)
            
            # Filtrar por rango de fechas
            if fecha_inicio:
                try:
                    fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                    query = query.filter(Curso.fecha_creacion >= fecha_inicio_dt)
                except ValueError:
                    return {'error': 'Formato de fecha_inicio inválido. Use YYYY-MM-DD'}, 400
            
            if fecha_fin:
                try:
                    fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
                    # Agregar un día para incluir todo el día final
                    fecha_fin_dt = fecha_fin_dt.replace(hour=23, minute=59, second=59)
                    query = query.filter(Curso.fecha_creacion <= fecha_fin_dt)
                except ValueError:
                    return {'error': 'Formato de fecha_fin inválido. Use YYYY-MM-DD'}, 400
            
            cursos = query.order_by(Curso.fecha_creacion.desc()).all()
            
            return {
                'cursos': [curso.to_dict() for curso in cursos],
                'total': len(cursos),
                'filtros_aplicados': {
                    'categoria': categoria_id,
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin
                }
            }, 200
            
        except Exception as e:
            return {'error': f'Error al obtener cursos: {str(e)}'}, 500

    def post(self):
        """Crear un nuevo curso"""
        try:
            data = request.get_json()
            
            # Validaciones
            if not data:
                return {'error': 'No se proporcionaron datos'}, 400
            
            campos_requeridos = ['nombre', 'categoria', 'precio']
            for campo in campos_requeridos:
                if campo not in data or data[campo] is None:
                    return {'error': f'El campo {campo} es requerido'}, 400
            
            # Validar que el precio sea positivo
            if data['precio'] < 0:
                return {'error': 'El precio debe ser mayor o igual a 0'}, 400
            
            # Verificar que la categoría exista
            categoria = Categoria.query.get(data['categoria'])
            if not categoria:
                return {'error': 'La categoría especificada no existe'}, 404
            
            # Crear curso
            nuevo_curso = Curso(
                nombre=data['nombre'],
                descripcion=data.get('descripcion', ''),
                categoria=data['categoria'],
                precio=data['precio']
            )
            
            db.session.add(nuevo_curso)
            db.session.commit()
            
            return {
                'message': 'Curso creado exitosamente',
                'curso': nuevo_curso.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Error al crear el curso: {str(e)}'}, 500


class CursoResource(Resource):
    def get(self, id):
        """Obtener un curso por ID"""
        try:
            curso = Curso.query.get(id)
            
            if not curso:
                return {'error': 'Curso no encontrado'}, 404
            
            return {'curso': curso.to_dict()}, 200
            
        except Exception as e:
            return {'error': f'Error al obtener el curso: {str(e)}'}, 500

    def put(self, id):
        """Actualizar un curso existente"""
        try:
            curso = Curso.query.get(id)
            
            if not curso:
                return {'error': 'Curso no encontrado'}, 404
            
            data = request.get_json()
            
            if not data:
                return {'error': 'No se proporcionaron datos'}, 400
            
            # Actualizar campos si se proporcionan
            if 'nombre' in data:
                curso.nombre = data['nombre']
            
            if 'descripcion' in data:
                curso.descripcion = data['descripcion']
            
            if 'categoria' in data:
                # Verificar que la categoría exista
                categoria = Categoria.query.get(data['categoria'])
                if not categoria:
                    return {'error': 'La categoría especificada no existe'}, 404
                curso.categoria = data['categoria']
            
            if 'precio' in data:
                if data['precio'] < 0:
                    return {'error': 'El precio debe ser mayor o igual a 0'}, 400
                curso.precio = data['precio']
            
            db.session.commit()
            
            return {
                'message': 'Curso actualizado exitosamente',
                'curso': curso.to_dict()
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Error al actualizar el curso: {str(e)}'}, 500

    def delete(self, id):
        """Eliminar un curso"""
        try:
            curso = Curso.query.get(id)
            
            if not curso:
                return {'error': 'Curso no encontrado'}, 404
            
            nombre_curso = curso.nombre
            db.session.delete(curso)
            db.session.commit()
            
            return {
                'message': f'Curso "{nombre_curso}" eliminado exitosamente'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Error al eliminar el curso: {str(e)}'}, 500
