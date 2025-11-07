import akshare as ak
import pandas as pd
current_date = pd.Timestamp.now().strftime("%Y%m%d")
szse_summary = ak.stock_szse_summary(date="20251107")
print(szse_summary)