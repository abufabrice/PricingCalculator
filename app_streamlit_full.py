import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title='Transport Pricing Simulator', layout='wide', page_icon='🚌')

lang = st.sidebar.radio("🌍 Language", ["English", "Français"])
is_french = lang == "Français"

modules_df = pd.read_csv('modules_config_clean.csv')
tiers_df = pd.read_csv('module_tiers_clean.csv')

categories = {
    "Booking Manager": "Booking & Sales",
    "Online Booking Manager": "Booking & Sales",
    "Parcel Manager": "Cargo & Parcel",
    "Expense Manager": "Finance",
    "Customer Communication Manager": "Customer Service",
    "Customer Support Personnel (External)": "Customer Service",
    "Maintenance Manager": "Fleet Operations",
    "Performance Optimization Tools": "Optimization",
    "HR Configuration Manager": "HR & Admin",
    "Fleet Configuration Manager": "Fleet Operations",
    "Procurement Manager": "Finance",
    "Accounting and Tax Manager": "Finance"
}

st.markdown(
    f"""
    <div style='background-color:#004d40;padding:20px;border-radius:10px;margin-bottom:20px;'>
        <h1 style='color:white;margin:0;'>🚌 Princesse Voyage Pricing Simulator</h1>
        <p style='color:#c8e6c9;font-size:16px;margin:0;'>{"Simulate your software costs in real-time" if not is_french else "Simulez vos coûts logiciels en temps réel"}</p>
    </div>
    """,
    unsafe_allow_html=True
)

admin_mode = st.sidebar.checkbox("🛠️ Admin Mode" if not is_french else "🛠️ Mode Admin")

module_col = 'Module'
type_col = 'Type'
price_col = 'UnitPrice'
tier_module_col = 'Module'
tier_threshold_col = 'Threshold'
tier_price_col = 'Price'

usage_inputs = {}
flat_prices = {}
tier_configs = {}

st.sidebar.subheader("📊 Module Usage" if not is_french else "📊 Utilisation des Modules")
for _, mod in modules_df.iterrows():
    module_name = str(mod[module_col])
    pricing_type = str(mod[type_col]).strip().lower()
    usage = st.sidebar.slider(module_name, 0, 1000, 0)
    usage_inputs[module_name] = usage

    if admin_mode:
        if pricing_type == 'flat':
            default_price = float(mod[price_col]) if pd.notna(mod[price_col]) else 0.0
            flat_prices[module_name] = st.sidebar.number_input(f"{module_name} Price", value=default_price, min_value=0.0)
        elif pricing_type == 'tiered':
            st.sidebar.markdown(f"**{module_name} – Tiered Pricing**")
            tier_data = tiers_df[tiers_df[tier_module_col] == module_name].copy()
            editable = st.sidebar.data_editor(tier_data.drop(columns=[tier_module_col]), key=f"tiers_{module_name}", num_rows="fixed")
            editable[tier_module_col] = module_name
            tier_configs[module_name] = editable
    else:
        if pricing_type == 'flat':
            flat_prices[module_name] = float(mod[price_col]) if pd.notna(mod[price_col]) else 0.0
        elif pricing_type == 'tiered':
            tier_configs[module_name] = tiers_df[tiers_df[tier_module_col] == module_name].copy()

records = []
for module_name, usage in usage_inputs.items():
    pricing_type = str(modules_df[modules_df[module_col] == module_name][type_col].values[0]).lower()
    cost = 0.0
    unit_price = None
    category = categories.get(module_name, "Other")

    if pricing_type == 'flat':
        unit_price = flat_prices.get(module_name, 0.0)
        cost = usage * unit_price
    elif pricing_type == 'tiered':
        tiers = tier_configs.get(module_name, pd.DataFrame())
        if not tiers.empty:
            finite = []
            infinite_price = None
            for _, t in tiers.iterrows():
                try:
                    thresh = float(t[tier_threshold_col])
                    price = float(t[tier_price_col])
                    finite.append((thresh, price))
                except:
                    infinite_price = float(t[tier]()_
