from flask import request
from flask import g
from flask_restful import Resource
import boto3
import hmac
import hashlib
import base64
import os
from botocore.exceptions import ClientError


def get_settings():
    return {
        'aws_region': os.getenv('AWS_REGION', 'us-east-2'),
        'cognito_user_pool_id': os.getenv('COGNITO_USER_POOL_ID', ''),
        'cognito_app_client_id': os.getenv('COGNITO_APP_CLIENT_ID', ''),
        'cognito_app_client_secret': os.getenv('COGNITO_APP_CLIENT_SECRET', '')
    }


def cognito_client():
    settings = get_settings()
    return boto3.client('cognito-idp', region_name=settings['aws_region'])


def secret_hash(username: str, app_client_id: str, app_client_secret: str) -> str:
    msg = username + app_client_id
    digest = hmac.new(
        app_client_secret.encode('utf-8'),
        msg=msg.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(digest).decode()


def with_secret_hash(params: dict, username: str, app_client_id: str, app_client_secret: str) -> dict:
    if app_client_secret:
        params['SECRET_HASH'] = secret_hash(username, app_client_id, app_client_secret)
    return params

class RegisterResource(Resource):
    def post(self):
        """Registra un usuario en Cognito"""
        try:
            settings = get_settings()
            cognito_user_pool_id = settings['cognito_user_pool_id']
            cognito_app_client_id = settings['cognito_app_client_id']
            cognito_app_client_secret = settings['cognito_app_client_secret']

            if not cognito_user_pool_id or not cognito_app_client_id:
                return {'error': 'Faltan variables COGNITO_USER_POOL_ID y/o COGNITO_APP_CLIENT_ID'}, 500

            data = request.get_json()
            if not data:
                return {'error': 'No se proporcionaron datos'}, 400

            correo = data.get('correo')
            password = data.get('contrasena')

            if not correo or not password:
                return {'error': 'correo y contrasena son requeridos'}, 400

            client = cognito_client()
            sign_up_payload = {
                'ClientId': cognito_app_client_id,
                'Username': correo,
                'Password': password,
                'UserAttributes': [
                    {'Name': 'email', 'Value': correo}
                ]
            }

            if cognito_app_client_secret:
                sign_up_payload['SecretHash'] = secret_hash(correo, cognito_app_client_id, cognito_app_client_secret)

            response = client.sign_up(**sign_up_payload)

            return {
                'message': 'Usuario registrado en Cognito',
                'user_sub': response.get('UserSub'),
                'user_confirmed': response.get('UserConfirmed', False)
            }, 201

        except ClientError as e:
            return {'error': e.response.get('Error', {}).get('Message', 'Error en Cognito')}, 400
        except Exception as e:
            return {'error': f'Error al registrar usuario: {str(e)}'}, 500


class LoginResource(Resource):
    def post(self):
        """Autentica usuario en Cognito y retorna tokens"""
        settings = get_settings()
        cognito_app_client_id = settings['cognito_app_client_id']
        cognito_app_client_secret = settings['cognito_app_client_secret']

        if not cognito_app_client_id:
            return {'error': 'Falta variable COGNITO_APP_CLIENT_ID'}, 500

        data = request.get_json()
        if not data:
            return {'error': 'No se proporcionaron datos'}, 400

        correo = data.get('correo')
        password = data.get('contrasena')

        if not correo or not password:
            return {'error': 'correo y contrasena son requeridos'}, 400

        try:
            client = cognito_client()
            auth_parameters = with_secret_hash({
                'USERNAME': correo,
                'PASSWORD': password
            }, correo, cognito_app_client_id, cognito_app_client_secret)

            response = client.initiate_auth(
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters=auth_parameters,
                ClientId=cognito_app_client_id
            )

            auth_result = response.get('AuthenticationResult', {})
            return {
                'message': 'Login exitoso',
                'access_token': auth_result.get('AccessToken'),
                'id_token': auth_result.get('IdToken'),
                'refresh_token': auth_result.get('RefreshToken'),
                'expires_in': auth_result.get('ExpiresIn'),
                'token_type': auth_result.get('TokenType', 'Bearer')
            }, 200
        except ClientError as e:
            return {'error': e.response.get('Error', {}).get('Message', 'Credenciales invalidas')}, 401
        except Exception as e:
            return {'error': f'Error en login: {str(e)}'}, 500


class RefreshTokenResource(Resource):
    def post(self):
        """Genera nuevos tokens usando refresh token de Cognito"""
        settings = get_settings()
        cognito_app_client_id = settings['cognito_app_client_id']
        cognito_app_client_secret = settings['cognito_app_client_secret']

        if not cognito_app_client_id:
            return {'error': 'Falta variable COGNITO_APP_CLIENT_ID'}, 500

        data = request.get_json() or {}
        refresh_token = data.get('refresh_token')
        correo = data.get('correo')

        if not refresh_token:
            return {'error': 'refresh_token es requerido'}, 400

        if cognito_app_client_secret and not correo:
            return {'error': 'correo es requerido cuando el app client tiene secret'}, 400

        try:
            client = cognito_client()
            auth_parameters = {
                'REFRESH_TOKEN': refresh_token
            }

            if cognito_app_client_secret and correo:
                auth_parameters = with_secret_hash(
                    auth_parameters,
                    correo,
                    cognito_app_client_id,
                    cognito_app_client_secret
                )

            response = client.initiate_auth(
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters=auth_parameters,
                ClientId=cognito_app_client_id
            )

            auth_result = response.get('AuthenticationResult', {})
            return {
                'message': 'Token refrescado',
                'access_token': auth_result.get('AccessToken'),
                'id_token': auth_result.get('IdToken'),
                'expires_in': auth_result.get('ExpiresIn'),
                'token_type': auth_result.get('TokenType', 'Bearer')
            }, 200
        except ClientError as e:
            return {'error': e.response.get('Error', {}).get('Message', 'No se pudo refrescar token')}, 401
        except Exception as e:
            return {'error': f'Error refrescando token: {str(e)}'}, 500


class MeResource(Resource):
    def get(self):
        """Retorna claims del token Cognito ya validado"""
        claims = getattr(g, 'cognito_claims', None)
        if not claims:
            return {'error': 'No autenticado'}, 401

        return {
            'usuario': {
                'sub': claims.get('sub'),
                'correo': claims.get('email') or claims.get('username') or claims.get('cognito:username'),
                'claims': claims
            }
        }, 200
