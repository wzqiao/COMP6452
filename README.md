# COMP6452 - Food Supply Chain Tracking System

A comprehensive food supply chain tracking system built with Flask (backend), React (frontend), and blockchain integration. This system enables transparent food traceability from production to consumption with secure role-based access control.

## 🌟 Features

### Core Functionality
- **Multi-Role Support**: Producer, Inspector, and Consumer roles with specific permissions
- **Batch Management**: Create and track food batches with detailed metadata
- **Quality Inspection**: Inspector-driven quality assurance with PDF report uploads
- **Blockchain Integration**: Immutable record-keeping using smart contracts
- **Supply Chain Transparency**: End-to-end traceability for consumers

### Technical Features
- JWT-based authentication with wallet binding
- SQLite database with SQLAlchemy ORM
- AWS S3 integration for PDF storage
- RESTful API design
- CORS-enabled cross-origin requests
- Docker containerization support

## 🏗️ System Architecture

### Backend (Flask)
- **Port**: 5000
- **Database**: SQLite (configurable)
- **Authentication**: JWT with role-based access
- **Smart Contracts**: BatchRegistry and InspectionManager

### Frontend (React + Vite)
- **Port**: 5173
- **Framework**: React with Vite build tool
- **Styling**: Bootstrap + Tailwind CSS
- **State Management**: React hooks

### Blockchain
- **Network**: Ethereum testnet
- **Contracts**: Solidity smart contracts for batch and inspection management
- **Wallet**: MetaMask integration

## 🚀 Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- MetaMask browser extension (for wallet features)

### Running the Application

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd COMP6452
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:5000

### Manual Setup (Development)

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
python app.py
```

#### Frontend Setup
```bash
cd fronted
npm install
npm run dev
```

## 👥 User Roles and Permissions

### Producer
- Create food batches with detailed metadata
- View own batch history
- Requires account registration and wallet binding

### Inspector
- View all pending batches
- Conduct quality inspections
- Upload PDF inspection reports
- Update inspection results (pass/fail)
- Requires account registration and wallet binding

### Consumer
- View all approved food batches
- Search and filter batches by various criteria
- Access inspection reports and blockchain records
- No registration required

## 📊 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/wallet` - Bind wallet address

### Batch Management
- `POST /batches` - Create new batch (Producer only)
- `GET /batches` - List all batches with filtering options
- `GET /batches/{id}` - Get specific batch details

### Inspection Management
- `POST /batches/{id}/inspections` - Submit inspection (Inspector only)
- `PUT /inspections/{id}` - Update inspection result
- `GET /inspections` - List all inspections

## 🗃️ Database Schema

### Users Table
- ID, email, password hash, role, wallet address

### Batches Table
- ID, batch number, product info, origin, quantity, dates
- Organic/import flags, status, blockchain transaction hash

### Inspections Table
- ID, batch reference, inspector, result, file URL
- Inspection date, blockchain transaction hash, notes

## 🔧 Configuration

### Environment Variables
```bash
# Flask Configuration
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=sqlite:///app.db

# AWS Configuration (for PDF uploads)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=ap-southeast-2
AWS_BUCKET_NAME=your-bucket-name
```

### Docker Configuration
The application includes:
- `backend/Dockerfile` - Python Flask application container
- `fronted/Dockerfile` - Node.js React application container
- `docker-compose.yml` - Multi-container orchestration

## 🔐 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-based Access Control**: Granular permissions by user role
- **CORS Configuration**: Controlled cross-origin access
- **Wallet Integration**: Blockchain wallet binding for verification
- **Input Validation**: Comprehensive data validation and sanitization

## 📋 Smart Contract Integration

### BatchRegistry Contract
- Creates immutable batch records on blockchain
- Stores batch metadata and ownership information
- Enables transparent supply chain tracking

### InspectionManager Contract
- Records inspection results on blockchain
- Maintains inspector accountability
- Provides tamper-proof quality assurance records

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/
```

### Smart Contract Tests
```bash
cd test
# Run with your preferred Solidity testing framework
```

## 📱 Frontend Features

### Authentication Flow
- Login/Register with role selection
- MetaMask wallet connection
- Automatic role-based UI adaptation

### Producer Dashboard
- Batch creation form with validation
- Date pickers for harvest/expiry dates
- Real-time submission feedback

### Inspector Dashboard
- Pending batch queue
- PDF upload functionality
- Inspection result submission

### Consumer Interface
- Public batch browser
- Advanced filtering options
- Inspection report viewing

## 🛠️ Development

### Project Structure
```
COMP6452/
├── backend/           # Flask API server
│   ├── models/        # Database models
│   ├── routes/        # API endpoints
│   ├── services/      # Business logic
│   └── contracts/     # Smart contracts
├── fronted/           # React frontend
│   └── src/           # React components
└── test/              # Smart contract tests
```

### Code Quality
- ESLint configuration for frontend
- Python code formatting standards
- Comprehensive error handling
- Input validation and sanitization

## 🚀 Deployment

### Production Considerations
- Use production-grade database (PostgreSQL recommended)
- Configure proper CORS origins
- Set secure JWT secrets
- Enable HTTPS
- Configure proper AWS credentials
- Set up monitoring and logging

### Scaling Options
- Load balancer for multiple backend instances
- Database connection pooling
- CDN for static assets
- Container orchestration (Kubernetes)

## 📝 License

This project is developed for COMP6452 coursework.

## 🤝 Contributing

This is an academic project. Please follow the course guidelines for any contributions or modifications.

---

For more detailed documentation, please refer to the individual README files in the `backend/` and `fronted/` directories.