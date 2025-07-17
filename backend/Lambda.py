import json
import boto3
import os
import jwt

s3 = boto3.client('s3')
JWT_SECRET = os.environ['JWT_SECRET_KEY']
BUCKET_NAME = os.environ['BUCKET_NAME']

CORS_HEADERS = {
    'Access-Control-Allow-Origin': 'http://localhost:5173',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'OPTIONS,POST'
}

def lambda_handler(event, context):
    try:
        # 验证 JWT 是否有效
        auth_header = event['headers'].get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
        decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = decoded['sub']
    except Exception as e:
        return {
            'statusCode': 401,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Invalid token'})
        }

    try:
        body = json.loads(event['body'])
        filename = body.get('filename')
        if not filename:
            raise ValueError("Missing filename")
    except:
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Missing filename'})
        }

    s3_key = f"{user_id}/{filename}"

    try:
        url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=300
        )
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': str(e)})
        }

    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps({'url': url})
    }
