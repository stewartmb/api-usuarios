import boto3
import json
from datetime import datetime

# Conexión a DynamoDB
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table('t_usuarios')
tokens_table = dynamodb.Table('t_tokens_acceso')

def validate_token(token):
    """
    Valida el token enviado en la solicitud.
    """
    response = tokens_table.get_item(Key={'token': token})
    if 'Item' not in response:
        raise Exception('Token no encontrado o inválido')

    token_data = response['Item']
    expires = token_data['expires']
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if now > expires:
        raise Exception('Token expirado')

    return token_data

def lambda_handler(event, context):
    try:
        # Validar si el header Authorization está presente
        headers = event.get('headers', {})
        authorization = headers.get('Authorization')

        if not authorization:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Authorization header no proporcionado'
                })
            }

        # Extraer el token
        token = authorization.replace('Bearer ', '')

        # Validar el token
        token_data = validate_token(token)

        # Extraer datos del token
        tenant_id = token_data['tenant_id']
        user_id = token_data['user_id']
        role = token_data['role']

        # Construir la clave para DynamoDB
        key = {
            'tenant_id#user_id': f"{tenant_id}#{user_id}",
            'role': role
        }

        # Consultar la tabla de usuarios
        response = users_table.get_item(Key=key)
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Usuario no encontrado.'
                })
            }

        user_data = response['Item']

        # Construir la respuesta del perfil del usuario
        user_profile = {
            'userId': user_id,
            'tenantId': tenant_id,
            'role': role,
            'email': user_data.get('email'),
            'specialty': user_data.get('specialty'),
            'status': user_data.get('status', 'unknown'),
            'gender': user_data.get('gender'),
            'fecha_nacimiento': user_data.get('fecha_nacimiento'),  # Actualizado
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name')
        }

        return {
            'statusCode': 200,
            'body': user_profile  # No es necesario volver a serializar aquí
        }

    except Exception as e:
        # Manejo de errores
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }
