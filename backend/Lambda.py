import json, os, boto3, jwt

s3 = boto3.client('s3')
JWT_SECRET  = os.environ['JWT_SECRET_KEY']
BUCKET_NAME = os.environ['BUCKET_NAME']

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "OPTIONS,POST"
}

def ok(body):  return {"statusCode": 200, "headers": CORS, "body": json.dumps(body)}
def err(code,msg): return {"statusCode": code, "headers": CORS, "body": json.dumps({"error": msg})}

def lambda_handler(event, _):
    m = event.get("requestContext", {}).get("http", {}).get("method")
    print("METHOD =", m)

    # 1) 预检
    if m == "OPTIONS":
        return {"statusCode": 200, "headers": CORS}

    # 2) 取并校验 JWT（大小写兼容）
    try:
        hdrs  = event.get("headers", {})
        token = (hdrs.get("Authorization") or hdrs.get("authorization") or "").replace("Bearer ", "")
        user  = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])["sub"]
    except Exception as e:
        print("JWT 失败:", e)
        return err(401, "invalid token")

    # 3) 解析 JSON body
    try:
        filename = json.loads(event.get("body","{}"))["filename"]
    except Exception as e:
        print("Body 失败:", e)
        return err(400, "missing filename")

    # 4) 生成 S3 预签名 URL
    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET_NAME, "Key": f"{user}/{filename}"},
        ExpiresIn=300
    )

    return ok({"url": url})
