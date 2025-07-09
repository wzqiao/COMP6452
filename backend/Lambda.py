import json
import boto3
import os
import jwt

s3 = boto3.client('s3')
JWT_SECRET = os.environ['JWT_SECRET_KEY']
BUCKET_NAME = os.environ['BUCKET_NAME']

def lambda_handler(event, context):
    try:
        # 验证 JWT 是否有效，获取 JWT token
        auth_header = event['headers'].get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
        decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = decoded['sub']  # Flask 默认 identity 会放在 sub 字段
    except Exception as e:
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Invalid token'})
        }

    # 获取上传文件名
    try:
        body = json.loads(event['body'])
        filename = body.get('filename')
        if not filename:
            raise ValueError("Missing filename")
    except:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing filename'})
        }

    # 构造 S3 上传路径：每个用户独立文件夹（按Flask里主键命目录名）
    s3_key = f"{user_id}/{filename}"

    try:
        url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=300  # 5分钟有效
        )
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'url': url})
    }
