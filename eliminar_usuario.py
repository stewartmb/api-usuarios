import boto3
import json
from botocore.exceptions import ClientError

# Inicializar DynamoDB
dynamodb = boto3.resource('dynamodb')
USERS_TABLE = "t_usuarios"

# Validar Token
def validate_token(token):
    lambda_client = boto3.client('lambda')
    try:
        response = lambda_client.invoke(
            FunctionName="ValidarTokenAcceso",
            InvocationType="RequestResponse",
            Payload=json.dumps({"token": token})
        )
        payload = response['Payload'].read().decode('utf-8')
        result = json.loads(payload)

        if result.get('statusCode') != 200:
            raise Exception(result.get('body', {}).get('error', 'Token inválido o expirado'))

        return result.get('body', {})
    except Exception as e:
        raise Exception(f"Error validando el token: {str(e)}")

def lambda_handler(event, context):
    try:
        # Validar token en los headers
        headers = event.get('headers', {})
        token = headers.get('Authorization', '').replace('Bearer ', '')

        if not token:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Token no proporcionado.'})
            }

        token_data = validate_token(token)

        # Verificar si el usuario tiene permisos
        if token_data.get('role') != 'admin':
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'No tiene permisos para eliminar usuarios.'})
            }

        # Extraer datos del body
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)

        tenant_id = body.get('tenant_id')
        user_id = body.get('user_id')
        role = body.get('role')  # Incluir el rol en el cuerpo de la solicitud

        if not tenant_id or not user_id or not role:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Faltan datos requeridos: tenant_id, user_id o role.'})
            }

        # Eliminar el usuario de DynamoDB
        table = dynamodb.Table(USERS_TABLE)
        try:
            table.delete_item(
                Key={
                    'tenant_id#user_id': f'{tenant_id}#{user_id}',
                    'role': role  # Incluir la clave de ordenación
                }
            )
        except ClientError as e:
            raise Exception(f"Error al eliminar el usuario: {str(e)}")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Usuario eliminado exitosamente.'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
