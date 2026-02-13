# Tethys AI Trading Platform - Local Setup

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB (local or Atlas)
- 16GB+ RAM recommended for ML

### 2. Install Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install Frontend
```bash
cd frontend
npm install  # or yarn install
```

### 4. Configure Environment

**backend/.env:**
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=tethys_trading
```

**frontend/.env:**
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

### 5. Restore Data
```bash
# Import all backed up data to MongoDB
mongorestore --db tethys_trading ./backups/
```

### 6. Run
```bash
# Terminal 1 - Backend
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

---

## ML Libraries (Install on your powerful machine)

The heavy ML dependencies that need your computer's power:

```bash
pip install tensorflow>=2.15.0
pip install keras>=3.0.0
pip install torch>=2.0.0
pip install scikit-learn>=1.3.0
pip install xgboost>=2.0.0
pip install lightgbm>=4.0.0
pip install stable-baselines3>=2.0.0
pip install gymnasium>=0.29.0
pip install transformers>=4.35.0
pip install pandas>=2.0.0
pip install numpy>=1.24.0
pip install ta>=0.10.0  # Technical analysis
```

---

## File Structure

```
tethys-local/
├── backend/
│   ├── server.py           # Main FastAPI app
│   ├── requirements.txt    # Python dependencies
│   ├── routes/             # API routes
│   ├── services/           # Business logic
│   ├── config/             # Configuration
│   └── .env                # Environment variables
├── frontend/
│   ├── src/                # React source
│   ├── package.json        # Node dependencies
│   └── .env                # Frontend config
├── backups/
│   └── [MongoDB dumps]     # Your historical data
├── ml_models/
│   └── [Trained models]    # Saved ML models
└── data/
    └── [Raw data files]    # Market data, news, etc.
```

---

## GPU Acceleration (Optional)

For faster ML training:

**NVIDIA GPU:**
```bash
pip install tensorflow[and-cuda]
# or
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

**Apple Silicon (M1/M2/M3):**
```bash
pip install tensorflow-metal
pip install torch torchvision torchaudio
```

---

## Docker Option (Easiest)

```bash
docker-compose up -d
```

This starts:
- MongoDB on port 27017
- Backend on port 8001
- Frontend on port 3000

---

## Data Locations

Your precious historical data:
- **Market Data**: `backups/historical_prices_*.json.gz`
- **News/Media**: `backups/social_sentiment_*.json.gz`
- **Training History**: `backups/historical_training_*.json.gz`
- **Patterns**: `backups/historical_patterns_*.json.gz`

---

## API Keys Needed

Add to `backend/.env`:
```
KRAKEN_API_KEY=your_key
KRAKEN_API_SECRET=your_secret
COINMARKETCAP_API_KEY=your_key
TWELVE_DATA_API_KEY=your_key
```

---

## Support

Test URL: https://launch-crypto-2.preview.emergentagent.com
