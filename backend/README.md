# Backend 进度

| 分组             | 方法   | 路径                              | 作用                               | 进度                  |
| -------------- | ---- | ------------------------------- | -------------------------------- | -------------------- |
| **Auth**       | POST | `/auth/register`                | 注册（邮箱＋密码）                        | ☑️                  |
|                | POST | `/auth/login`                   | 登录、发 JWT                         | ☑️                 |
|                | POST | `/auth/wallet`                  | 绑定钱包地址                           | ☑️ |
| **File**       | POST | `https://wvdam1xz7a.execute-api.ap-southeast-2.amazonaws.com/default/UploadPdf_6452`                       | 生成 S3 预签名 URL                    | ☑️         |
| **Batch**      | POST | `/batches`                      | 创建批次（metadata）                   | processing             |
|                | GET  | `/batches/{id}`            | 查询单批次详情（metadata＋inspections）    | processing                 |
| **Inspection** | POST | `/batches/{id}/inspection` | 提交检验结果 `pass│fail` ＋ PDF URL，并写链 | processing            |

**关于pdf upload的API**
预签名的生成服务和返回交给lambda + API Gateway处理了，利用token对称加密，环境变量设置暂时与config.py中保持同步，后续.env最后提交再修改

该服务与本地flask独立，可以直接测试，ApiFox中说明已更新。


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
│   ├─ s3_service.py     # 已删除，改用lambda + API Gateway托管服务
│   ├─ blockchain.py     # 组合 web3 调合约；供 inspection.py 调
│   └─ batch_service.py  # 辅助元数据校验、状态更新
│
├─ migrations/
│
├─ Lambda.py              #托管函数，与本地flask无关
│
├─ test_auth.sh           # Auth任务下3个API的模拟测试，模拟发送 HTTP 请求
│
└─ init_db.py            # 开发阶段暂时用的SQLite，后边再migration
```