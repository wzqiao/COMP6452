# Food Supply Chain Management System - Frontend

A modern food supply chain management system frontend application built with React + Vite, providing complete business process support for three roles: producers, inspectors, and consumers.

## 🚀 Project Features

### 📱 Multi-Role Support
- **Producer**: Create and manage food batches, upload product information
- **Inspector**: View pending inspection batches, submit inspection results
- **Consumer**: Query product information, trace supply chain processes

### 🔐 Security Authentication
- JWT Token authentication
- Blockchain wallet binding (for producers and inspectors)
- Role-based access control

### 🎨 Modern UI Design
- Responsive design with mobile support
- Bootstrap + Tailwind CSS dual styling framework
- Lucide React icon library
- Intuitive user interface and interaction experience

### 🔗 Blockchain Integration
- Seamless interaction with smart contracts
- Data transparency and traceability
- Decentralized trust mechanism

## 🛠️ Tech Stack

### Core Framework
- **React 19.1.0** - User interface construction
- **Vite 7.0.4** - Fast build tool
- **React Router DOM 7.6.3** - Route management

### UI Components and Styling
- **Bootstrap 5.3.7** - UI component library
- **Tailwind CSS 4.1.11** - Styling framework
- **Lucide React 0.525.0** - Icon library
- **React DatePicker 8.4.0** - Date picker

### Development Tools
- **ESLint 9.30.1** - Code quality checking
- **PostCSS & Autoprefixer** - CSS processing
- **TypeScript definitions** - Type support

## 📁 Project Structure

```
fronted/
├── public/                 # Static assets
│   └── vite.svg
├── src/                   # Source code
│   ├── assets/           # Asset files
│   ├── App.jsx           # Main application component
│   ├── main.jsx          # Application entry
│   ├── LoginRegister.jsx # Login/register page
│   ├── WalletBindModal.jsx # Wallet binding modal
│   ├── ProducerPage.jsx  # Producer page
│   ├── InspectorPage.jsx # Inspector page
│   ├── ConsumerPage.jsx  # Consumer page
│   └── InspectionDetailPage.jsx # Inspection detail page
├── index.html            # HTML template
├── package.json          # Project configuration
├── vite.config.js        # Vite configuration
└── eslint.config.js      # ESLint configuration
```

## 🚀 Quick Start

### Environment Requirements
- Node.js >= 16.0.0
- npm >= 7.0.0

### Install Dependencies
```bash
cd fronted
npm install
```

### Development Mode
```bash
npm run dev
```
Application will start at http://localhost:5173

### Build Production Version
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

### Code Linting
```bash
npm run lint
```

## 📋 Feature Modules

### 🔑 User Authentication (LoginRegister.jsx)
- Email/password registration and login support
- Three user role selection
- Consumer login-free access
- JWT Token management

### 💼 Producer Features (ProducerPage.jsx)
- **Batch Creation**: Input basic product information
  - Batch number, product name, origin
  - Quantity, unit, harvest date, expiry date
  - Organic certification, import labels
- **Form Validation**: Ensure data integrity
- **Submit Feedback**: Real-time operation results

### 🔍 Inspector Features (InspectorPage.jsx)
- **Batch List**: View all pending inspection batches
- **Status Filtering**: Filter by inspection status
- **Inspection Operations**: Direct navigation to inspection detail page
- **Pagination Loading**: Support browsing large amounts of data

### 👥 Consumer Features (ConsumerPage.jsx)
- **Product Query**: 
  - Search by batch ID
  - Filter by inspection results
  - Filter by organic/import attributes
- **Information Display**: 
  - Batch basic information
  - Inspection status and results
  - Timestamp formatting display
- **Supply Chain Tracing**: View complete product flow records

### 🔗 Wallet Binding (WalletBindModal.jsx)
- MetaMask wallet connection
- Blockchain address binding
- Required security verification steps

### 📝 Inspection Details (InspectionDetailPage.jsx)
- Detailed inspection information display
- Inspection result management
- File upload and viewing

## 🔧 Configuration

### Vite Configuration (vite.config.js)
```javascript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    watch: {
      usePolling: true, // File change monitoring
    },
  },
})
```

### API Interface Configuration
- Backend API address: `http://127.0.0.1:5000`
- Supported interfaces:
  - `/auth/login` - User login
  - `/auth/register` - User registration
  - `/batches` - Batch management
  - `/inspections` - Inspection management

## 🎯 User Workflows

### Producer Workflow
1. Register/login to system
2. Bind blockchain wallet
3. Create new product batch
4. Fill in detailed product information
5. Submit to blockchain network

### Inspector Workflow
1. Register/login to system
2. Bind blockchain wallet
3. View pending inspection batch list
4. Select batch for inspection
5. Submit inspection results

### Consumer Workflow
1. Direct access to system (no login required)
2. Enter product batch number or use filters
3. View detailed product information
4. Understand complete supply chain process

## 🔒 Security Features

- **Authentication**: JWT Token secure authentication
- **Access Control**: Role-based access control
- **Data Validation**: Frontend form validation and backend API validation
- **Blockchain Security**: Wallet signature verification
- **HTTPS Support**: Secure transmission in production environment

## 🐛 Development & Debugging

### Common Issue Resolution
1. **Port Conflict**: Modify port number in `vite.config.js`
2. **API Connection Failure**: Check if backend service is running
3. **Wallet Connection Issues**: Ensure MetaMask extension is installed

### Development Tools
- React Developer Tools
- Vite DevTools
- Browser console debugging

## 🚀 Deployment

### Build Optimization
```bash
npm run build
```

### Deploy to Production Environment
1. Build production version
2. Deploy `dist` directory to web server
3. Configure reverse proxy to backend API
4. Enable HTTPS certificates

## 📝 Changelog

### v1.0.0
- Initial version release
- Complete three-role functionality support
- Blockchain integration
- Responsive UI design

## 🤝 Contributing

1. Fork the project
2. Create feature branch
3. Commit code changes
4. Push to branch
5. Create Pull Request

## 📄 License

This project is licensed under the MIT License
