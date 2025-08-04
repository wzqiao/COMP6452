# Backend Progress

## API Progress

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

## PDF Upload API

The pre-signed-URL service is handled by **AWS Lambda + API Gateway**.  
Symmetric tokens are used for encryption; environment variables are currently mirrored in `config.py` and will be moved to `.env` before the final commit.

This service is independent of the local Flask app and can be tested directly. See the updated description in **ApiFox**.

## Batch & Inspection API Implementation

- Completed batch and inspection data models with full field definitions and relationships.  
- Implemented complete batch management APIs for creation and querying.  
- Implemented full inspection APIs for submission, querying, updating, etc.  
- Integrated blockchain service to store inspection results on-chain.  
- Added JWT authentication and role-based access control.  
- Performed comprehensive tests to validate the entire workflow.

## Blockchain Integration

- Developed Solidity smart contracts: **`BatchRegistry.sol`** and **`InspectionManager.sol`**.  
- Implemented a full blockchain service (`blockchain.py`) using **Web3.py**.  
- Enabled on-chain storage and retrieval for batch and inspection data.  
- Integrated Ethereum network interaction via Web3.py.

## Front-End Local Startup

1. Clone the repository.  
2. Run `pip install -r requirements.txt`.  
3. Run `python init_db.py` to initialize the SQLite database.  
4. Run `python app.py` to start the Flask server.

## Backend Reference Structure

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
