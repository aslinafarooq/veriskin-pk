import streamlit as st
from supabase import create_client
from google import genai
from google.genai import types

# 1. Page Setup & Disclaimer
st.set_page_config(page_title="VeriSkin PK", layout="wide")
st.title("VeriSkin PK — Verified Skincare & Community Insights")
st.info(
    "**Disclaimer:** VeriSkin is an informational decision-support tool powered by "
    "community experiences and retailer data—it is not a medical professional and can make "
    "mistakes. Always consult a licensed dermatologist for skin conditions or treatments."
)

# 2. Initialize Clients (from Streamlit Secrets)
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
gemini = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# 3. Simple Code Guardrail for Clinical / Medical Queries
MEDICAL_KEYWORDS = ["diagnose", "prescription", "eczema", "psoriasis", "infection", "bleeding", "severe rash", "steroid"]

def is_medical_query(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in MEDICAL_KEYWORDS)

# 4. User Search Input
query = st.text_input("Search a skincare product, ingredient, or concern (e.g., niacinamide serum under 3000 PKR):")

if query:
    if is_medical_query(query):
        st.warning(
            "It looks like you're asking about a medical skin condition or prescription treatment. "
            "VeriSkin only compares verified retailer listings and general user experiences—please consult a licensed dermatologist."
        )
    else:
        with st.spinner("Checking verified retailers and community insights..."):
            # Retrieve rows from Supabase (adjust column names if your schema differs)
            products = supabase.table("products").select("*").ilike("name", f"%{query}%").limit(5).execute().data
            if not products:
                # Fallback: fetch recent rows so Gemini can inspect available catalog items
                products = supabase.table("products").select("*").limit(10).execute().data

            sources = supabase.table("product_sources").select("*").limit(15).execute().data
            retailers = supabase.table("retailers").select("*").limit(15).execute().data
            reddit = supabase.table("reddit_insights").select("*").limit(15).execute().data

            context_block = f"""
            PRODUCTS: {products}
            PRODUCT_SOURCES: {sources}
            RETAILERS: {retailers}
            REDDIT_INSIGHTS: {reddit}
            """

            system_prompt = (
                "You are VeriSkin PK, a consumer-trust assistant for skincare shoppers in Pakistan. "
                "Answer ONLY using the provided Supabase database records (products, product_sources, retailers, reddit_insights). "
                "Include PKR prices and verified retailer names/links when present in the records. "
                "Summarize real user experiences from reddit_insights honestly, including both pros and cons. "
                "If a product or detail is not in the records, explicitly say you do not have verified data for it. "
                "Never diagnose medical conditions or recommend prescription treatments."
            )

            response = gemini.models.generate_content(
                model="gemini-3.8-flash",
                contents=f"User Question: {query}\n\nDatabase Records:\n{context_block}",
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2,
                ),
            )

            st.subheader("VeriSkin Summary")
            st.markdown(response.text)

            with st.expander("View Raw Verified Database Records"):
                st.write("**Products:**", products)
                st.write("**Product Sources:**", sources)
                st.write("**Retailers:**", retailers)
                st.write("**Reddit Insights:**", reddit)
