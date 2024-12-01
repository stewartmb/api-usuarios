import boto3
import hashlib
from datetime import datetime, timedelta
import uuid

# Función para hashear la contraseña
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    try:
        # Extraer los datos del evento
        tenant_id = event.get('tenant_id')
        user_id = event.get('user_id')
        password = event.get('password')
        role = event.get('role')  # Ahora también se pasa el role en la entrada

        # Validar que todos los campos requeridos estén presentes
        if not tenant_id or not user_id or not password or not role:
            return {
                'statusCode': 400,
                'body': {'error': 'Faltan tenant_id, user_id, password o role'}
            }

        # Hashear la contraseña ingresada
        hashed_password = hash_password(password)

        # Conectar a DynamoDB
        dynamodb = boto3.resource('dynamodb')
        t_usuarios = dynamodb.Table('t_usuarios')

        # Construir la clave para buscar al usuario
        key = {
            'tenant_id#user_id': f"{tenant_id}#{user_id}",
            'role': role  # Usar el role proporcionado como clave de ordenamiento
        }

        # Obtener los datos del usuario
        response = t_usuarios.get_item(Key=key)

        if 'Item' not in response:
            return {
                'statusCode': 403,
                'body': {'error': 'Usuario no encontrado o clave incorrecta'}
            }

        # Validar la contraseña
        stored_password = response['Item']['password']
        if hashed_password != stored_password:
            return {
                'statusCode': 403,
                'body': {'error': 'Contraseña incorrecta'}
            }

        # Generar un token único
        token = str(uuid.uuid4())
        expiration_time = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')

        # Guardar el token en la tabla de tokens
        t_tokens_acceso = dynamodb.Table('t_tokens_acceso')
        t_tokens_acceso.put_item(
            Item={
                'token': token,
                'expires': expiration_time,
                'tenant_id': tenant_id,
                'user_id': user_id,
                'role': role
            }
        )

        # Devolver la respuesta con el token y el rol
        return {
            'statusCode': 200,
            'body': {
                'message': 'Login exitoso',
                'token': token,
                'role': role
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }
