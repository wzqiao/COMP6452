# Backend Progress / 后端进度

<!-- Language Toggle / 语言切换 -->
**Language / 语言**: [English](#english) | [中文](#中文)

---

## English

### API Progress

| Group        | Method | Path                                                                                                                    | Purpose                                                                     | Status |
|--------------|--------|-------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|--------|
| **Auth**     | POST   | `/auth/register`                                                                                                        | Register (email + password)                                                  | ✅ |
|              | POST   | `/auth/login`                                                                                                           | Login & issue JWT                                                           | ✅ |
|              | POST   | `/auth/wallet`                                                                                                          | Bind wallet address                                                         | ✅ |
| **File**     | POST   | `https://wvdam1xz7a.execute-api.ap-southeast-2.amazonaws.com/default/UploadPdf_6452`                                    | Generate S3 pre-signed URL                                                  | ✅ |
|              | PUT    | `{url response from Lambda}`                                                                                            | Upload PDF file                                                             | ✅ |
| **Batch**    | POST   | `/batches`                                                                                                              | Create batch (metadata)                                                     | ✅ |
|              | GET    | `/batches/{id}`                                                                                                         | Get batch details (metadata + inspections)                                  | ✅ |
| **Inspection** | POST | `/batches/{id}/inspection`                                                                                              | Submit result (`pass│fail`) + PDF URL; write to chain                       | ✅ |
|              | GET    | `/batches/{id}/inspections`                                                                                             | List inspections for a batch                                               | ✅ |
|              | GET    | `/inspections/{id}`                                                                                                     | Get inspection details                                                      | ✅ |
|              | PUT    | `/inspections/{id}`                                                                                                     | Update inspection record                                                    | ✅ |
|              | GET    | `/inspections`                                                                                                          | Paginated inspection list                                                   | ✅ |

### PDF Upload API

The pre-signed-URL service is handled by **AWS Lambda + API Gateway**.  
Symmetric tokens are used for encryption; environment variables are currently mirrored in `config.py` and will be moved to `.env` before the final commit.

This service is independent of the local Flask app and can be tested directly. See the updated description in **ApiFox**.

### Batch & Inspection API Implementation

- Completed batch and inspection data models with full field definitions and relationships.  
- Implemented complete batch management APIs for creation and querying.  
- Implemented full inspection APIs for submission, querying, updating, etc.  
- Integrated blockchain service to store inspection results on-chain.  
- Added JWT authentication and role-based access control.  
- Performed comprehensive tests to validate the entire workflow.

### Blockchain Integration

- Developed Solidity smart contracts: **`BatchRegistry.sol`** and **`InspectionManager.sol`**.  
- Implemented a full blockchain service (`blockchain.py`) using **Web3.py**.  
- Enabled on-chain storage and retrieval for batch and inspection data.  
- Integrated Ethereum network interaction via Web3.py.

### Front-End Local Startup

1. Clone the repository.  
2. Run `pip install -r requirements.txt`.  
3. Run `python init_db.py` to initialize the SQLite database.  
4. Run `python app.py` to start the Flask server.

### Backend Reference Structure

```text
backend/
├─ app.py                     # Flask app
├─ config.py
├─ requirements.txt           # Python dependencies
├─ .env
│
├─ extensions/                # Third-party extensions initialization
│   └─ __init__.py            # db / jwt / boto3.client(...)
│
├─ models/                    # ORM mappings
│   ├─ __init__.py
│   ├─ user.py                # User(id, email, pw_hash, role, wallet)
│   ├─ batch.py               # Batch(id, metadata(JSON), status, created_at, owner_id)
│   └─ inspection.py          # Inspection(id, batch_id, result, file_url, insp_date)
│
├─ routes/                    # Pure routing layer (grouped by API)
│   ├─ __init__.py
│   ├─ auth.py               # /auth/login  /auth/register  /auth/wallet
│   ├─ storage.py            # /upload  (generate pre-signed S3 URL)
│   ├─ batch.py              # /batches  POST + GET <batchId>
│   └─ inspection.py         # Complete Inspection API (POST, GET, PUT) + blockchain integration
│
├─ services/                  # Business logic (no core logic in routes)
│   ├─ __init__.py
│   ├─ s3_service.py         # Removed; replaced by Lambda + API Gateway managed service
│   ├─ blockchain.py         # Full Web3 integration service + smart contract interaction
│   └─ batch_service.py      # Complete batch business logic + state management
│
├─ contracts/                 # Smart contracts
│   ├─ BatchRegistry.sol      # Batch registration contract
│   ├─ InspectionManager.sol  # Inspection management contract
│   ├─ deploy_config.py       # Deployment configuration
│   └─ README.md              # Contract documentation
│
├─ migrations/
│
├─ Lambda.py                  # Hosted function, independent of local Flask
│
├─ test_auth.sh               # Simulated HTTP requests for Auth APIs
├─ test_inspection_api.py     # Inspection API integration tests
├─ services/test_blockchain.py # Blockchain service tests
│
└─ init_db.py                 # SQLite initialization (development stage; migrations later)
```

---

## 中文

### API 进度

| 分组             | 方法   | 路径                              | 作用                               | 进度                  |
| -------------- | ---- | ------------------------------- | -------------------------------- | -------------------- |
| **Auth**       | POST | `/auth/register`                | 注册（邮箱＋密码）                        | ✅                  |
|                | POST | `/auth/login`                   | 登录、发 JWT                         | ✅                 |
|                | POST | `/auth/wallet`                  | 绑定钱包地址                           | ✅ |
| **File**       | POST | `https://wvdam1xz7a.execute-api.ap-southeast-2.amazonaws.com/default/UploadPdf_6452`                       | 生成 S3 预签名 URL                    | ✅         |
| |PUT | `{url response from lambda}` | 上传pdf文件的地址| ✅ |
| **Batch**      | POST | `/batches`                      | 创建批次（metadata）                   | ✅             |
|                | GET  | `/batches/{id}`            | 查询单批次详情（metadata＋inspections）    | ✅                 |
| **Inspection** | POST | `/batches/{id}/inspection` | 提交检验结果 `pass│fail` ＋ PDF URL，并写链 | ✅            |
|                | GET  | `/batches/{id}/inspections`| 获取批次检验记录列表                      | ✅            |
|                | GET  | `/inspections/{id}`        | 获取检验记录详情                         | ✅            |
|                | PUT  | `/inspections/{id}`        | 更新检验记录                           | ✅            |
|                | GET  | `/inspections`             | 检验记录列表（分页）                      | ✅            |

### 关于 PDF Upload API

预签名的生成服务和返回交给 **Lambda + API Gateway** 处理了，利用token对称加密，环境变量设置暂时与config.py中保持同步，后续.env最后提交再修改。

该服务与本地flask独立，可以直接测试，ApiFox中说明已更新。

### 关于 Batch 和 Inspection API 的实现

- 完善了批次和检验数据模型，包含完整的字段定义和关联关系
- 实现了完整的批次管理API，支持创建、查询批次信息
- 实现了完整的检验API，支持检验结果提交、查询、更新等操作
- 集成了区块链服务，支持检验结果上链存储
- 添加了JWT认证和角色权限控制
- 完成了综合测试，验证了完整的业务流程

### 区块链集成

- 开发了Solidity智能合约（**`BatchRegistry.sol`**, **`InspectionManager.sol`**）
- 实现了完整的区块链服务（`blockchain.py`）使用 **Web3.py**
- 支持批次和检验数据的链上存储和查询
- 集成了以太坊网络交互

### 前端调试启动

1. Pull 代码仓库
2. 终端运行 `pip install -r requirements.txt`
3. 终端运行 `python init_db.py` 初始化 SQLite 数据库
4. 终端运行 `python app.py` 启动 Flask 服务器

### 后端参考结构

```text
backend/
├─ app.py                 # Flask 实例
├─ config.py
├─ requirements.txt       # freeze出的依赖
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
│   └─ inspection.py     # ✅ 完整的检验API (POST, GET, PUT) + 区块链集成
│
├─ services/              # 业务服务（路由不写核心逻辑）
│   ├─ __init__.py
│   ├─ s3_service.py     # 已删除，改用lambda + API Gateway托管服务
│   ├─ blockchain.py     # ✅ 完整的Web3集成服务 + 智能合约交互
│   └─ batch_service.py  # ✅ 完善的批次业务逻辑 + 状态管理
│
├─ contracts/             # ✅ 智能合约开发
│   ├─ BatchRegistry.sol      # 批次注册合约
│   ├─ InspectionManager.sol  # 检验管理合约
│   ├─ deploy_config.py       # 部署配置
│   └─ README.md              # 合约说明文档
│
├─ migrations/
│
├─ Lambda.py              # 托管函数，与本地flask无关
│
├─ test_auth.sh           # Auth任务下3个API的模拟测试，模拟发送 HTTP 请求
├─ test_inspection_api.py # ✅ 检验API集成测试
├─ services/test_blockchain.py # ✅ 区块链服务测试
│
└─ init_db.py            # 开发阶段暂时用的SQLite，后边再migration
```

---

**[⬆ Back to Top / 返回顶部](#backend-progress--后端进度)**
