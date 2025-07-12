# Backend 进度

| 分组             | 方法   | 路径                              | 作用                               | 进度                  |
| -------------- | ---- | ------------------------------- | -------------------------------- | -------------------- |
| **Auth**       | POST | `/auth/register`                | 注册（邮箱＋密码）                        | ☑️                  |
|                | POST | `/auth/login`                   | 登录、发 JWT                         | ☑️                 |
|                | POST | `/auth/wallet`                  | 绑定钱包地址                           | ☑️ |
| **File**       | POST | `https://wvdam1xz7a.execute-api.ap-southeast-2.amazonaws.com/default/UploadPdf_6452`                       | 生成 S3 预签名 URL                    | ☑️         |
| **Batch**      | POST | `/batches`                      | 创建批次（metadata）                   | ☑️             |
|                | GET  | `/batches/{id}`            | 查询单批次详情（metadata＋inspections）    | ☑️                 |
| **Inspection** | POST | `/batches/{id}/inspection` | 提交检验结果 `pass│fail` ＋ PDF URL，并写链 | ☑️            |
|                | GET  | `/batches/{id}/inspections`| 获取批次检验记录列表                      | ☑️            |
|                | GET  | `/inspections/{id}`        | 获取检验记录详情                         | ☑️            |
|                | PUT  | `/inspections/{id}`        | 更新检验记录                           | ☑️            |
|                | GET  | `/inspections`             | 检验记录列表（分页）                      | ☑️            |

**关于pdf upload的API**
预签名的生成服务和返回交给lambda + API Gateway处理了，利用token对称加密，环境变量设置暂时与config.py中保持同步，后续.env最后提交再修改

该服务与本地flask独立，可以直接测试，ApiFox中说明已更新。

**关于Batch和Inspection API的实现**
- 完善了批次和检验数据模型，包含完整的字段定义和关联关系
- 实现了完整的批次管理API，支持创建、查询批次信息
- 实现了完整的检验API，支持检验结果提交、查询、更新等操作
- 集成了区块链服务，支持检验结果上链存储
- 添加了JWT认证和角色权限控制
- 完成了综合测试，验证了完整的业务流程

**区块链集成**
- 开发了Solidity智能合约（BatchRegistry.sol, InspectionManager.sol）
- 实现了完整的区块链服务（blockchain.py）
- 支持批次和检验数据的链上存储和查询
- 集成了Web3.py进行以太坊网络交互

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
│   └─ inspection.py     # ☑️ 完整的检验API (POST, GET, PUT) + 区块链集成
│
├─ services/              # 业务服务（路由不写核心逻辑）
│   ├─ __init__.py
│   ├─ s3_service.py     # 已删除，改用lambda + API Gateway托管服务
│   ├─ blockchain.py     # ☑️ 完整的Web3集成服务 + 智能合约交互
│   └─ batch_service.py  # ☑️ 完善的批次业务逻辑 + 状态管理
│
├─ contracts/             # ☑️ 智能合约开发
│   ├─ BatchRegistry.sol      # 批次注册合约
│   ├─ InspectionManager.sol  # 检验管理合约
│   ├─ deploy_config.py       # 部署配置
│   └─ README.md              # 合约说明文档
│
├─ migrations/
│
├─ Lambda.py              #托管函数，与本地flask无关
│
├─ test_auth.sh           # Auth任务下3个API的模拟测试，模拟发送 HTTP 请求
├─ test_inspection_api.py # ☑️ 检验API集成测试
├─ services/test_blockchain.py # ☑️ 区块链服务测试
│
└─ init_db.py            # 开发阶段暂时用的SQLite，后边再migration
```