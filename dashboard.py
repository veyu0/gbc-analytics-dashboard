import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
import altair as alt

# Настройки Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("Аналитика заказов")

# Получение данных из Supabase
@st.cache_data
def load_orders():
	response = supabase.table("orders").select("order_id, created_at, total_sum").execute()
	if response.data:
		df = pd.DataFrame(response.data)
		df["created_at"] = pd.to_datetime(df["created_at"])
		df["total_sum"] = pd.to_numeric(df["total_sum"], errors="coerce")
		return df
	else:
		return pd.DataFrame(columns=["order_id", "created_at", "total_sum"])

df = load_orders()

if df.empty:
	st.warning("Нет данных о заказах.")
else:
	st.subheader("Гистограмма по сумме заказа")
	hist = alt.Chart(df).mark_bar().encode(
		alt.X("total_sum", bin=alt.Bin(maxbins=20), title="Сумма заказа"),
		y=alt.Y("count()", title="Количество заказов"),
		tooltip=["total_sum"]
	).properties(width=700, height=300)
	st.altair_chart(hist, use_container_width=True)

	st.subheader("Распределение заказов по статусу")
	if "status" in df.columns:
		status_counts = df["status"].value_counts().reset_index()
		status_counts.columns = ["status", "count"]
		pie = alt.Chart(status_counts).mark_arc(innerRadius=50).encode(
			theta=alt.Theta(field="count", type="quantitative"),
			color=alt.Color(field="status", type="nominal"),
			tooltip=["status", "count"]
		).properties(width=400, height=400)
		st.altair_chart(pie, use_container_width=False)
		st.dataframe(status_counts)
	else:
		st.info("Нет данных о статусах заказов.")

	st.subheader("Топ городов по количеству заказов")
	if "city" in df.columns:
		city_counts = df["city"].value_counts().reset_index()
		city_counts.columns = ["city", "count"]
		bar = alt.Chart(city_counts).mark_bar().encode(
			x=alt.X("city", sort='-y', title="Город"),
			y=alt.Y("count", title="Количество заказов"),
			tooltip=["city", "count"]
		).properties(width=700, height=400)
		st.altair_chart(bar, use_container_width=True)
		st.dataframe(city_counts)
	else:
		st.info("Нет данных о городах заказов.")
