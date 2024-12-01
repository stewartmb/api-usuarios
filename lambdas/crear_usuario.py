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
        tenant_id = event.get('tenant_id')
        user_id = event.get('user_id')
        password = event.get('password')
        role = event.get('role')
        specialty = event.get('specialty')
        email = event.get('email')
        gender = event.get('gender')  # Nuevo atributo
        fecha_nacimiento = event.get('fecha_nacimiento')  # Nuevo atributo
        first_name = event.get('first_name')  # Nuevo atributo
        last_name = event.get('last_name')  # Nuevo atributo

        # Validar que los campos requeridos estén presentes
        if not tenant_id or not user_id or not password or not role or not specialty or not email or not gender or not fecha_nacimiento or not first_name or not last_name:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Faltan tenant_id, user_id, password, role, specialty, email, gender, fecha_nacimiento, first_name o last_name.'
                })
            }

        # Validar formato de fecha de nacimiento
        if not validate_date(fecha_nacimiento):
            return {
                'statusCode': 400,
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
            'tenant_id#user_id': f"{tenant_id}#{user_id}",  # Clave de partición
            'role': role,  # Clave de ordenamiento
            'password': hashed_password,
            'specialty': specialty,
            'email': email,
            'gender': gender,
            'fecha_nacimiento': fecha_nacimiento,  # Almacenar fecha_nacimiento
            'first_name': first_name,
            'last_name': last_name
        }

        # Insertar el usuario en la tabla
        t_usuarios.put_item(Item=user_item)

        return {
            'statusCode': 200,
            'body': {
                'message': 'Usuario registrado exitosamente',
                'user_id': user_id
            }
        }
    except Exception as e:
        # Manejo de errores
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }
