from flask import request
from flask_restful import Resource
from models import db
from models.usuario import Usuario
from models.categoria import Categoria
from models.curso import Curso

class SeedDemoResource(Resource):
    def post(self):
        """Inserta datos de prueba para usuarios, categorias y cursos"""
        try:
            payload = request.get_json(silent=True) or {}
            limpiar = bool(payload.get('limpiar', False))

            if limpiar:
                Curso.query.delete()
                Categoria.query.delete()
                Usuario.query.delete()
                db.session.commit()

            usuarios_data = [
                {'correo': 'admin@demo.com', 'contrasena': 'Admin123*'},
                {'correo': 'estudiante@demo.com', 'contrasena': 'Estudiante123*'}
            ]

            categorias_data = [
                {'nombre': 'Programacion', 'descripcion': 'Cursos de desarrollo de software'},
                {'nombre': 'Diseno', 'descripcion': 'Cursos de UX/UI y herramientas visuales'},
                {'nombre': 'Marketing', 'descripcion': 'Cursos de marketing digital'}
            ]

            usuarios_creados = 0
            categorias_creadas = 0
            cursos_creados = 0

            for item in usuarios_data:
                existente = Usuario.query.filter_by(correo=item['correo']).first()
                if existente:
                    continue

                usuario = Usuario(correo=item['correo'])
                usuario.set_password(item['contrasena'])
                db.session.add(usuario)
                usuarios_creados += 1

            db.session.commit()

            categorias_map = {}
            for item in categorias_data:
                existente = Categoria.query.filter_by(nombre=item['nombre']).first()
                if existente:
                    categorias_map[item['nombre']] = existente
                    continue

                categoria = Categoria(nombre=item['nombre'], descripcion=item['descripcion'])
                db.session.add(categoria)
                db.session.flush()
                categorias_map[item['nombre']] = categoria
                categorias_creadas += 1

            db.session.commit()

            cursos_data = [
                {
                    'nombre': 'Python desde cero',
                    'descripcion': 'Fundamentos de Python para principiantes',
                    'categoria': 'Programacion',
                    'precio': 49.99
                },
                {
                    'nombre': 'Flask API REST',
                    'descripcion': 'Construccion de APIs con Flask y buenas practicas',
                    'categoria': 'Programacion',
                    'precio': 79.99
                },
                {
                    'nombre': 'UX Research',
                    'descripcion': 'Introduccion a investigacion de usuarios',
                    'categoria': 'Diseno',
                    'precio': 59.99
                },
                {
                    'nombre': 'Marketing en Redes Sociales',
                    'descripcion': 'Estrategias para crecer en plataformas sociales',
                    'categoria': 'Marketing',
                    'precio': 39.99
                }
            ]

            for item in cursos_data:
                existente = Curso.query.filter_by(nombre=item['nombre']).first()
                if existente:
                    continue

                categoria_obj = categorias_map.get(item['categoria'])
                if not categoria_obj:
                    continue

                curso = Curso(
                    nombre=item['nombre'],
                    descripcion=item['descripcion'],
                    categoria=categoria_obj.id,
                    precio=item['precio']
                )
                db.session.add(curso)
                cursos_creados += 1

            db.session.commit()

            return {
                'message': 'Seeder ejecutado correctamente',
                'resumen': {
                    'usuarios_creados': usuarios_creados,
                    'categorias_creadas': categorias_creadas,
                    'cursos_creados': cursos_creados,
                    'limpieza_aplicada': limpiar
                },
                'credenciales_demo': [
                    {'correo': 'admin@demo.com', 'contrasena': 'Admin123*'},
                    {'correo': 'estudiante@demo.com', 'contrasena': 'Estudiante123*'}
                ]
            }, 200

        except Exception as e:
            db.session.rollback()
            return {'error': f'Error al ejecutar seeder: {str(e)}'}, 500
