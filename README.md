# 🔥 meradOS Heatmap

**Stock Market Intelligence Platform** - Real-time market heatmap, stock analysis, and screening tool.

![meradOS Heatmap](https://img.shields.io/badge/meradOS-Heatmap-667eea?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-3776ab?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-ff4b4b?style=flat-square&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## ✨ Features

### 🗺️ Market Heatmap
- **Interactive Treemap** - Finviz-style visualization of market sectors
- **Color-coded performance** - Instant view of gainers/losers
- **Sector breakdown** - Technology, Finance, Healthcare, Energy, etc.
- **Real-time data** - Updates every 5 minutes

### 📊 Stock Analysis
- **100-Point Scoring System** - Comprehensive stock rating
- **DCF Fair Value** - Intrinsic value calculation
- **Technical Charts** - Candlestick with SMA overlays
- **Peer Comparison** - Compare against competitors

### 🔍 Stock Screener
- **Custom Filters** - P/E, Dividend, Growth, Beta
- **Preset Strategies** - Value, Growth, Dividend, Momentum
- **Sortable Results** - Find the best stocks quickly

### 📰 News Feed
- **Latest Headlines** - Per-stock news aggregation
- **Publisher Info** - Source and timestamp
- **Direct Links** - One-click to full article

### 📋 Watchlist
- **Personal Tracking** - Add/remove tickers
- **Live Updates** - Real-time price changes
- **Performance Chart** - Compare watchlist stocks

## 🚀 Quick Start

### Local Installation

```bash
# Clone the repository
git clone https://github.com/merados/heatmap.git
cd heatmap

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

Open http://localhost:8501 in your browser.

### Docker

```bash
docker build -t merados-heatmap .
docker run -p 8501:8501 merados-heatmap
```

## 🌐 Deploy to Vercel

1. Fork this repository
2. Connect to [Vercel](https://vercel.com)
3. Import the repository
4. Deploy!

Or use the button:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/merados/heatmap)

## 📊 Scoring System

The 100-point scoring system evaluates stocks across 6 dimensions:

| Category | Max Points | Metrics |
|----------|------------|---------|
| **Valuation** | 25 | P/E, PEG, P/B |
| **Profitability** | 25 | Profit Margin, ROE |
| **Growth** | 20 | Revenue & Earnings Growth |
| **Financial Health** | 15 | Debt/Equity, Current Ratio |
| **Dividend** | 10 | Yield |
| **Analyst** | 5 | Recommendations |

### Rating Scale

| Score | Rating | Meaning |
|-------|--------|---------|
| 75%+ | 🟢 STRONG BUY | Excellent |
| 60-74% | 🟢 BUY | Good |
| 45-59% | 🟡 HOLD | Average |
| 30-44% | 🟠 SELL | Below Average |
| <30% | 🔴 STRONG SELL | Poor |

## 🔧 Configuration

Edit `.streamlit/config.toml` for customization:

```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
```

## 📁 Project Structure

```
merados-heatmap/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── config.toml       # Streamlit configuration
├── README.md             # This file
└── LICENSE               # MIT License
```

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Charts**: [Plotly](https://plotly.com/python/)
- **Data**: [Yahoo Finance (yfinance)](https://github.com/ranaroussi/yfinance)
- **Processing**: [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)

## 📈 Data Sources

| Source | Data Type | Update Frequency |
|--------|-----------|------------------|
| Yahoo Finance | Price, Fundamentals | Real-time |
| Yahoo Finance | News | 10 min cache |
| Calculated | Scores, DCF | On-demand |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [Finviz](https://finviz.com/map.ashx) Market Map
- Built with [Streamlit](https://streamlit.io/)
- Data from [Yahoo Finance](https://finance.yahoo.com/)

## 📬 Contact

- GitHub: [@merados](https://github.com/merados)
- Project: [meradOS Heatmap](https://github.com/merados/heatmap)

---

<p align="center">
  <strong>🔥 meradOS Heatmap</strong><br>
  <sub>Built with ❤️ for traders and investors</sub>
</p>
