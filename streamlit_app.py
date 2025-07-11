import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import japanize_matplotlib
import streamlit as st
import newspaper
from newspaper import Article
import nltk
from nltk.tokenize import word_tokenize
import time
import re

nltk.download('punkt', quiet = True)

st.set_page_config(page_title = "大阪市　物件過熱度ダッシュボード", layout = "wide")

#不動産データ
try:
    df = pd.read_csv("data/raw/used_redata.csv", encoding="932")
    df = df.rename(columns = {"市区町村名" : "area", "取引価格（総額）" : "price", "取引時期" : "year", "最寄駅：距離（分）" : "distance", "建築年" : "built_year"})
    df["year"] = df["year"].apply(lambda x:int(re.search(r'\d{4}', str(x)).group()) if re.search(r'\d{4}', str(x)) else None)
    if df["year"].isnull().any():
        st.warning("「year（取引時期）」列に無効な値があります。該当行を削除します。")
        df["year"] = df["year"].astype("int64")
except FileNotFoundError:
    st.error("不動産データが見つかりません！仮データを使用します")
    data = {
        'area': ['大阪市中央区', '大阪市中央区', '大阪市北区', '大阪市北区', '大阪市天王寺区', '大阪市天王寺区', '大阪市福島区', '大阪市福島区'],
        '取引価格（総額）': [7500, 9000, 6500, 7800, 6000, 6800, 5000, 5500], 
        '取引時期': [2020, 2024, 2020, 2024, 2020, 2024, 2020, 2024], 
        '最寄駅：距離（分）': [3, 3, 4, 4, 5, 5, 4, 4], 
        '建築年': [2010, 2010, 2008, 2008, 2005, 2005, 2000, 2000]
    }
    df = pd.DataFrame(data)


#Xムードデータ
x_mood = {
    'area': ['大阪市中央区', '大阪市北区', '大阪市天王寺区', '大阪市福島区'], 
    'x_buzz_score': [80, 60, 40, 20]
}
df_x = pd.DataFrame(x_mood)


#データ処理
#駅徒歩10分以内の物件をフィルタリング
df['distance'] = pd.to_numeric(df['distance'],  errors='coerce') #数値へ変換
df_station_near = df[df['distance'] <= 10]
price_trend = df_station_near.groupby(['area', 'year'])['price'].mean().reset_index()
price_trend_pivot = df_station_near.groupby(['area', 'year'])['price'].mean().unstack()

#エリアごとの価格上昇率を計算
try:
    price_trend_pivot['growth_rate'] = ((price_trend_pivot[2024] - price_trend_pivot[2020]) / price_trend_pivot[2020]) * 100
except KeyError as e:
    st.error(f"データに2020年または2024年がありません。: {e}")
    st.write("利用可能な年：", price_trend_pivot.columns.tolist())
    price_trend_pivot['growth_rate'] = 0 #エラー回避
 
# Xムードデータと統合
overheat_score = price_trend_pivot[['growth_rate']].reset_index()
overheat_score = overheat_score.merge(df_x, on = 'area', how = 'left')

#streamlitでダッシュボード構築
st.title("大阪市内　駅近物件の過熱度ダッシュボード")

# スパゲッティプロット
st.subheader("エリアごとの価格推移(スパゲッティプロット)")
st.write("表示するエリアを選択してください")
areas = df_station_near["area"].unique()
selected_areas = []
for area in areas:
    if st.checkbox(area, value = True, key = f"area_{area}"): 
        selected_areas.append(area)

fig, ax = plt.subplots(figsize = (10, 6))
colors = sns.color_palette("rainbow", len(selected_areas))
for i, area in enumerate(selected_areas):
    area_data = price_trend[price_trend['area'] == area]
    if area_data.empty:
        st.warning(f"{area}のデータが空です。")
        continue
    ax.plot(area_data["year"], area_data["price"], label = area, marker = 'o', color = colors[i])
ax.set_title("エリアごとの物件価格推移")
ax.set_xlabel("年")
ax.set_ylabel("平均価格（千万円）")
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True)
st.pyplot(fig)

#スライダーで価格上昇率の閾値選択
threshold = st.slider("過熱エリアの閾値(価格上昇率%)", 0, 100, 30)

#ヒートマップ
st.subheader("エリアごとの価格上昇率ヒートマップ(2020-2024)")
fig, ax = plt.subplots(figsize = (8, 16))
heatmap_data = overheat_score.pivot_table(index = 'area', values = 'growth_rate')
sns.heatmap(heatmap_data, annot = True, cmap = 'coolwarm', fmt = '.1f', ax = ax)
ax.set_title('価格上昇率(%) - 大阪市内駅近物件')
ax.set_ylabel('エリア')
ax.set_xlabel('指標')
st.pyplot(fig)

#過熱エリアのテーブル
st.subheader(f"過熱エリア(価格上昇率 {threshold}%以上)")
hot_areas = overheat_score[overheat_score['growth_rate'] > threshold][['area', 'growth_rate', 'x_buzz_score']]
hot_areas = hot_areas.sort_values(by = 'growth_rate', ascending = False)
st.table(hot_areas.rename(columns = {'area':'エリア', 'growth_rate':'価格上昇率(%)', 'x_buzz_score':'Xバズりスコア'}))

#Xムードの解説
st.subheader("Xの市場ムード")
st.write("Xバズりスコアは、X投稿の「再開発」や「物件」関連の話題量を簡易的に数値化(100点満点)。高いほど注目度大！")
for _, row in hot_areas.iterrows():
    st.write(f"{row['area']}: Xバズりスコア{row['x_buzz_score']} - 再開発や駅近物件の話題が{'盛ん' if row['x_buzz_score'] > 50 else '普通'}")