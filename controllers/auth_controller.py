from flask import request
from flask_restful import Resource
from flask_jwt_extended import create_access_token
from flask_jwt_extended import create_refresh_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from models import db
from models.usuario import Usuario

class RegisterResource(Resource):
    def post(self):
        """Crea un usuario con contrasena hasheada"""
        try:
            data = request.get_json()
            if not data:
                return {'error': 'No se proporcionaron datos'}, 400

            correo = data.get('correo')
            password = data.get('contrasena')

            if not correo or not password:
                return {'error': 'correo y contrasena son requeridos'}, 400

            existing = Usuario.query.filter_by(correo=correo).first()
            if existing:
                return {'error': 'Ya existe un usuario con ese correo'}, 409

            usuario = Usuario(correo=correo)
            usuario.set_password(password)

            db.session.add(usuario)
            db.session.commit()

            return {
                'message': 'Usuario creado exitosamente',
                'usuario': usuario.to_dict()
            }, 201

        except Exception as e:
            db.session.rollback()
            return {'error': f'Error al crear usuario: {str(e)}'}, 500


class LoginResource(Resource):
    def post(self):
        """Autentica usuario y retorna JWT"""

        data = request.get_json()
        if not data:
            return {'error': 'No se proporcionaron datos'}, 400

        correo = data.get('correo')
        password = data.get('contrasena')

        if not correo or not password:
            return {'error': 'correo y contrasena son requeridos'}, 400

        usuario = Usuario.query.filter_by(correo=correo).first()
        if not usuario or not usuario.check_password(password):
            return {'error': 'Credenciales invalidas'}, 401

        access_token = create_access_token(identity=str(usuario.id))
        refresh_token = create_refresh_token(identity=str(usuario.id))

        return {
            'message': 'Login exitoso',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'usuario': usuario.to_dict()
        }, 200


class RefreshTokenResource(Resource):
    @jwt_required(refresh=True)
    def post(self):
        """Genera un nuevo access token usando refresh token JWT"""
        user_id = get_jwt_identity()
        access_token = create_access_token(identity=user_id)
        return {
            'message': 'Token refrescado',
            'access_token': access_token,
            'token_type': 'Bearer'
        }, 200


class MeResource(Resource):
    @jwt_required()
    def get(self):
        """Obtiene el usuario autenticado con JWT"""
        user_id = get_jwt_identity()
        usuario = Usuario.query.get(int(user_id))

        if not usuario:
            return {'error': 'Usuario no encontrado'}, 404

        return {
            'usuario': usuario.to_dict()
        }, 200
