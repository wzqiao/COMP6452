# Backend 进度

| 分组             | 方法   | 路径                              | 作用                               | 进度                  |
| -------------- | ---- | ------------------------------- | -------------------------------- | -------------------- |
| **Auth**       | POST | `/auth/register`                | 注册（邮箱＋密码）                        | ☑️                  |
|                | POST | `/auth/login`                   | 登录、发 JWT                         | ☑️                 |
|                | POST | `/auth/wallet`                  | 绑定钱包地址                           | ☑️ |
| **File**       | POST | `/upload`                       | 生成 S3 预签名 URL                    | processing          |
| **Batch**      | POST | `/batches`                      | 创建批次（metadata）                   | processing             |
|                | GET  | `/batches/{id}`            | 查询单批次详情（metadata＋inspections）    | processing                 |
| **Inspection** | POST | `/batches/{id}/inspection` | 提交检验结果 `pass│fail` ＋ PDF URL，并写链 | processing            |




## 前端调试启动
1. pull repo，
2. 终端`pip install -r requirements.txt`
3. 终端`python init_db.py`
4. 终端`python app.py`





## 后端B参考
```
项目文件结构
backend/
├─ app.py                 # Flask 实例
├─ config.py
├─ requirements.txt       #freeze出的依赖
├─ .env
│
├─ extensions/            # 第三方扩展初始化
│   └─ __init__.py        # db / jwt / boto3.client(...)
│
├─ models/                # ORM 映射
│   ├─ __init__.py
│   ├─ user.py            # User(id, email, pw_hash, role, wallet)
│   ├─ batch.py           # Batch(id, metadata(JSON), status, created_at, owner_id)
│   └─ inspection.py      # Inspection(id, batch_id, result, file_url, insp_date)
│
├─ routes/                # 纯路由层（按 API 分）
│   ├─ __init__.py
│   ├─ auth.py           # /auth/login  /auth/register  /auth/wallet
│   ├─ storage.py        # /upload  （生成 S3 预签名 URL）
│   ├─ batch.py          # /batches  POST + GET <batchId>
│   └─ inspection.py     # /batches/<id>/inspection  POST
│
├─ services/              # 业务服务（路由不写核心逻辑）
│   ├─ __init__.py
│   ├─ s3_service.py     # 生成预签名；供 storage.py 调
│   ├─ blockchain.py     # 组合 web3 调合约；供 inspection.py 调
│   └─ batch_service.py  # 辅助元数据校验、状态更新
│
├─ migrations/
│
├─test_auth.sh           # Auth任务下3个API的模拟测试，模拟发送 HTTP 请求
│
└─ init_db.py            # 开发阶段暂时用的SQLite，后边再migration
```