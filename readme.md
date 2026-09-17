🛍️ Retail Sales Analytics Dashboard — Complete
Project Structure
Retail sales/
├── Retail_Sales_Analytics_Project_Dataset.xlsx   ← your data
└── retail_dashboard/
    ├── data_processor.py    ← Python backend
    ├── app.py               ← Streamlit frontend
    └── requirements.txt     ← dependencies

How to Run
# from the workspace root (Desktop\Retail sales)
streamlit run retail_dashboard/app.py

Architecture
Backend — data_processor.py

Reads all 4 sheets: Raw_Sales, Customers, Products, Monthly_Targets
Full data cleaning: deduplication, whitespace normalisation, date parsing, invalid discount handling ("Unknown" → 0), region/channel case normalisation
Pre-computes 10 analytical DataFrames cached for the UI: KPIs, monthly trends, category/region/channel/segment performance, top products, rep leaderboard, payment mix, city rankings
Frontend — app.py — Streamlit + Plotly

Tab	Charts
📈 Trends	Dual-axis revenue/profit bar+line, day-of-week bar, order scatter, rolling 3M margin
🗺️ Geography	Region horizontal bars, profit margin bars, top-15 cities grouped bar, Region×Category heat map, Channel split per region
📦 Products & Categories	Revenue donut, margin bars, top-10 products coloured by margin, revenue vs profit bubble, discount box plots, quantity area chart
👥 Segments & Channels	Segment donut, dual-axis channel chart, Segment×Region heat map, payment pie, margin by segment×category
🏆 Leaderboard	Rep horizontal bar, styled data table, 8-rep radar chart, rep revenue vs profit scatter, full data explorer with CSV export
Global Sidebar Filters: Year · Region · Category · Segment · Sales Channel — all charts update live.

Verified KPIs from your dataset: ₹22.9 Cr revenue · 2,192 orders · 497 unique customers · ₹3.72 avg ship days
