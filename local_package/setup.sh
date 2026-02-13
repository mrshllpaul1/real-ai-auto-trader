#!/bin/bash
# Tethys Local Setup Script
# Run this on your local computer after downloading

echo "🚀 Setting up Tethys AI Trading Platform..."

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js required"; exit 1; }

# Extract package
echo "📦 Extracting files..."
tar -xzf tethys_full_package.tar.gz

# Setup backend
echo "🐍 Setting up Python backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install ML libraries (the heavy ones)
echo "🧠 Installing ML libraries (this takes a while)..."
pip install tensorflow keras torch scikit-learn xgboost lightgbm
pip install stable-baselines3 gymnasium transformers

# Setup frontend
echo "⚛️ Setting up React frontend..."
cd ../frontend
npm install

# Create .env files
echo "⚙️ Creating config files..."
cd ..

cat > backend/.env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=tethys_trading
EOF

cat > frontend/.env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
EOF

# Restore data
echo "💾 Restoring backed up data..."
cd backups
tar -xzf backups.tar.gz

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start:"
echo "  1. Start MongoDB: mongod"
echo "  2. Backend: cd backend && source venv/bin/activate && uvicorn server:app --port 8001"
echo "  3. Frontend: cd frontend && npm run dev"
echo ""
echo "Open http://localhost:3000 in your browser"
