import streamlit as st
from supabase import create_client

st.set_page_config(page_title="VeriSkin PK", layout="wide")
st.title("VeriSkin PK — Verified Skincare & Community Insights")
st.caption("Informational only — not medical advice. Always consult a licensed dermatologist.")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

products = supabase.table("products").select("*").limit(5).execute()
st.subheader("Sample Products from Database")
st.dataframe(products.data)
