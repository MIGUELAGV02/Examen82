from flask import Flask
from flask import jsonify
from flask import request
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_jwt_extended import verify_jwt_in_request
from flask_cors import CORS
from flask_restful import Api
from flask_swagger_ui import get_swaggerui_blueprint
import os
from models import db
from models.categoria import Categoria
from models.curso import Curso
from models.usuario import Usuario
from controllers.categoria_controller import CategoriaCreateResource, CategoriaListResource
from controllers.curso_controller import CursoListResource, CursoResource
from controllers.auth_controller import RegisterResource, LoginResource, MeResource
from controllers.seed_controller import SeedDemoResource

# Crear aplicación Flask
app = Flask(__name__)


PUBLIC_PATHS = {
    '/api/auth/login',
    '/api/auth/login/',
    '/api/auth/register',
    '/api/auth/register/',
    '/api/swagger.json'
}
PUBLIC_PREFIXES = ('/docs',)


@app.before_request
def require_jwt_for_protected_routes():
    if request.method == 'OPTIONS':
        return None

    if request.path in PUBLIC_PATHS:
        return None

    if any(request.path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
        return None

    if request.path.startswith('/api'):
        verify_jwt_in_request()

    return None


@app.route('/api')
@app.route('/api/')
def api_index():
    return {
        'message': 'Base de la API',
        'documentacion': '/docs',
        'endpoints': {
            'categorias': '/api/categorias',
            'cursos': '/api/courses',
            'auth': '/api/auth',
            'seed': '/api/seed'
        }
    }

# Configuración
# Prioriza una URI completa si está definida en entorno.
# Si no existe, construye conexión a MySQL con la BD `cursos`.
db_uri = os.getenv('DATABASE_URL')
if not db_uri:
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME', 'cursos')
    db_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'cambia-esto-en-produccion')

# Inicializar SQLAlchemy
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
CORS(app)


@jwt.unauthorized_loader
def unauthorized_response(reason):
    return {'error': reason}, 401


@jwt.invalid_token_loader
def invalid_token_response(reason):
    return {'error': reason}, 401


@jwt.expired_token_loader
def expired_token_response(jwt_header, jwt_payload):
    return {'error': 'Token expirado'}, 401

api_errors = {
    'NoAuthorizationError': {
        'message': 'Missing Authorization Header',
        'status': 401
    },
    'InvalidHeaderError': {
        'message': 'Authorization header invalido',
        'status': 401
    },
    'JWTDecodeError': {
        'message': 'Token invalido',
        'status': 401
    }
}

api = Api(app, prefix='/api', errors=api_errors)

api.add_resource(CategoriaCreateResource, '/categorias')
api.add_resource(CategoriaListResource, '/categorias/all')
api.add_resource(CursoListResource, '/courses')
api.add_resource(CursoResource, '/courses/<int:id>')
api.add_resource(RegisterResource, '/auth/register')
api.add_resource(LoginResource, '/auth/login')
api.add_resource(MeResource, '/auth/me')
api.add_resource(SeedDemoResource, '/seed/demo')


def swagger_spec():
    return {
        'openapi': '3.0.3',
        'info': {
            'title': 'API de Gestion de Cursos',
            'version': '1.0.0',
            'description': 'Documentacion de API con Flask-RESTful y Swagger UI'
        },
        'servers': [
            {'url': '/'}
        ],
        'components': {
            'securitySchemes': {
                'BearerAuth': {
                    'type': 'http',
                    'scheme': 'bearer',
                    'bearerFormat': 'JWT'
                }
            }
        },
        'security': [{'BearerAuth': []}],
        'paths': {
            '/api/categorias': {
                'post': {
                    'summary': 'Crear categoria',
                    'requestBody': {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'required': ['nombre'],
                                    'properties': {
                                        'nombre': {'type': 'string'},
                                        'descripcion': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    },
                    'responses': {'201': {'description': 'Categoria creada'}}
                }
            },
            '/api/categorias/all': {
                'get': {
                    'summary': 'Listar categorias',
                    'responses': {'200': {'description': 'OK'}}
                }
            },
            '/api/courses': {
                'get': {
                    'summary': 'Listar cursos',
                    'responses': {'200': {'description': 'OK'}}
                },
                'post': {
                    'summary': 'Crear curso',
                    'requestBody': {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'required': ['nombre', 'categoria', 'precio'],
                                    'properties': {
                                        'nombre': {'type': 'string'},
                                        'descripcion': {'type': 'string'},
                                        'categoria': {'type': 'integer'},
                                        'precio': {'type': 'number'}
                                    }
                                }
                            }
                        }
                    },
                    'responses': {'201': {'description': 'Curso creado'}}
                }
            },
            '/api/courses/{id}': {
                'get': {
                    'summary': 'Obtener curso',
                    'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
                    'responses': {'200': {'description': 'OK'}}
                },
                'put': {
                    'summary': 'Actualizar curso',
                    'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
                    'responses': {'200': {'description': 'Curso actualizado'}}
                },
                'delete': {
                    'summary': 'Eliminar curso',
                    'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
                    'responses': {'200': {'description': 'Curso eliminado'}}
                }
            },
            '/api/auth/register': {
                'post': {
                    'summary': 'Registrar usuario',
                    'security': [],
                    'requestBody': {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'required': ['correo', 'contrasena'],
                                    'properties': {
                                        'correo': {'type': 'string'},
                                        'contrasena': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    },
                    'responses': {'201': {'description': 'Usuario creado'}}
                }
            },
            '/api/auth/login': {
                'post': {
                    'summary': 'Login',
                    'security': [],
                    'requestBody': {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'required': ['correo', 'contrasena'],
                                    'properties': {
                                        'correo': {'type': 'string'},
                                        'contrasena': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    },
                    'responses': {'200': {'description': 'Token generado'}}
                }
            },
            '/api/auth/me': {
                'get': {
                    'summary': 'Perfil autenticado',
                    'security': [{'BearerAuth': []}],
                    'responses': {'200': {'description': 'OK'}}
                }
            },
            '/api/seed/demo': {
                'post': {
                    'summary': 'Cargar datos de prueba',
                    'requestBody': {
                        'required': False,
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'limpiar': {'type': 'boolean'}
                                    }
                                }
                            }
                        }
                    },
                    'responses': {'200': {'description': 'Seeder ejecutado'}}
                }
            }
        }
    }


@app.route('/api/swagger.json')
def swagger_json():
    return jsonify(swagger_spec())


swagger_blueprint = get_swaggerui_blueprint(
    '/docs',
    '/api/swagger.json',
    config={'app_name': 'API de Gestion de Cursos'}
)
app.register_blueprint(swagger_blueprint, url_prefix='/docs')


# Ruta de bienvenida
@app.route('/')
def index():
    return {
        'message': 'API de Gestión de Cursos',
        'version': '1.0',
        'documentacion': '/docs',
        'endpoints': {
            'categorias': '/api/categorias',
            'cursos': '/api/courses',
            'auth': '/api/auth',
            'seed': '/api/seed'
        }
    }


# Manejadores de errores globales
@app.errorhandler(404)
def not_found(error):
    return {'error': 'Recurso no encontrado'}, 404


@app.errorhandler(500)
def internal_error(error):
    return {'error': 'Error interno del servidor'}, 500


@app.errorhandler(400)
def bad_request(error):
    return {'error': 'Solicitud inválida'}, 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
