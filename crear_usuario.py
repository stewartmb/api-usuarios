import boto3
import hashlib
import json
from datetime import datetime

# Función para hashear la contraseña
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Validar formato de fecha
def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def lambda_handler(event, context):
    try:
        # Extraer los datos del evento
        body = json.loads(event.get('body', '{}'))  # Deserializa el cuerpo de la solicitud
        tenant_id = body.get('tenant_id')
        user_id = body.get('user_id')
        password = body.get('password')
        role = body.get('role')
        specialty = body.get('specialty')
        email = body.get('email')
        gender = body.get('gender')
        fecha_nacimiento = body.get('fecha_nacimiento')
        first_name = body.get('first_name')
        last_name = body.get('last_name')

        # Validar que los campos requeridos estén presentes
        if not tenant_id or not user_id or not password or not role or not specialty or not email or not gender or not fecha_nacimiento or not first_name or not last_name:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Faltan tenant_id, user_id, password, role, specialty, email, gender, fecha_nacimiento, first_name o last_name.'
                })
            }

        # Validar formato de fecha de nacimiento
        if not validate_date(fecha_nacimiento):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'El formato de fecha_nacimiento debe ser YYYY-MM-DD.'
                })
            }

        # Hashear la contraseña
        hashed_password = hash_password(password)

        # Conectar a DynamoDB
        dynamodb = boto3.resource('dynamodb')
        t_usuarios = dynamodb.Table('t_usuarios')

        # Crear el objeto del usuario con las claves primarias y atributos adicionales
        user_item = {
            'tenant_id#user_id': f"{tenant_id}#{user_id}",
            'role': role,
            'password': hashed_password,
            'specialty': specialty,
            'email': email,
            'gender': gender,
            'fecha_nacimiento': fecha_nacimiento,
            'first_name': first_name,
            'last_name': last_name
        }

        # Insertar el usuario en la tabla
        t_usuarios.put_item(Item=user_item)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Usuario registrado exitosamente',
                'user_id': user_id
            })
        }
    except Exception as e:
        # Manejo de errores
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }
