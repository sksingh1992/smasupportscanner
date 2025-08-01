# 📈 Intraday Bounce Scanner (IST)

## 📌 Files
- `main.py` → Streamlit scanner app
- `config.json` → Add your SmartAPI credentials
- `requirements.txt` → All libraries
- `Procfile` → Required for Render deployment
- `test_dixon.py` → For backtest on Dixon example

## 🚀 How to Deploy
1. Go to [Render](https://render.com)
2. Create a new Web Service
3. Connect GitHub repository (or upload manually)
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `streamlit run main.py --server.port $PORT --server.address 0.0.0.0`
6. Deploy ✅

