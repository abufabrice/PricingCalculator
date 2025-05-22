import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title='Transport Pricing Simulator', layout='wide', page_icon='🚌')

lang = st.sidebar.radio("🌍 Language", ["English", "Français"])
is_french = lang == "Français"

DEFAULT_CONFIG = 'modules_config_matched.csv'
CONFIG_KEY = 'live_config'

# Load config from CSV only once per session
if CONFIG_KEY not in st.session_state:
    st.session_state[CONFIG_KEY] = pd.read_csv(DEFAULT_CONFIG)

modules_df = st.session_state[CONFIG_KEY]
tiers_df = pd.read_csv('module_tiers_clean.csv')

# Optional: business logic for grouping
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
        <h1 style='color:white;margin:0;'>🚌 Ongoing Pricing Simulator</h1>
        <p style='color:#c8e6c9;font-size:16px;margin:0;'>{"Simulate the software costs for your digital transformation in real-time" if not is_french else "Simulez vos coûts logiciels en temps réel"}</p>
    </div>
    """,
    unsafe_allow_html=True
)

admin_mode = st.sidebar.checkbox("🛠️ Admin Mode" if not is_french else "🛠️ Mode Admin")

usage_inputs = {}
flat_prices = {}
tier_configs = {}
updated_usage_settings = []

st.sidebar.subheader("📊 Module Usage" if not is_french else "📊 Utilisation des Modules")

# MAIN CONFIG LOOP
for _, mod in modules_df.iterrows():
    module_name = str(mod["Module"])
    pricing_type = str(mod["Type"]).strip().lower()

    default_usage = int(mod["DefaultUsage"]) if not pd.isna(mod["DefaultUsage"]) else 100
    max_usage = int(mod["MaxUsage"]) if not pd.isna(mod["MaxUsage"]) else default_usage * 2

    if admin_mode:
        st.sidebar.markdown(f"**{module_name} Config**")
        default_usage = st.sidebar.number_input(f"Default usage for {module_name}", min_value=0, value=default_usage, key=f"default_{module_name}")
        max_usage = st.sidebar.number_input(f"Max usage for {module_name}", min_value=default_usage, value=max_usage, key=f"max_{module_name}")
        updated_usage_settings.append((module_name, default_usage, max_usage))

    usage = st.sidebar.slider(module_name, 0, max_usage, default_usage, key=f"slider_{module_name}")
    usage_inputs[module_name] = usage

    if admin_mode:
        if pricing_type == 'flat':
            default_price = float(mod["UnitPrice"]) if pd.notna(mod["UnitPrice"]) else 0.0
            flat_prices[module_name] = st.sidebar.number_input(f"{module_name} Price", value=default_price, min_value=0.0)
        elif pricing_type == 'tiered':
            st.sidebar.markdown(f"**{module_name} – Tiered Pricing**")
            tier_data = tiers_df[tiers_df["Module"] == module_name].copy()
            editable = st.sidebar.data_editor(tier_data.drop(columns=["Module"]), key=f"tiers_{module_name}", num_rows="fixed")
            editable["Module"] = module_name
            tier_configs[module_name] = editable
    else:
        if pricing_type == 'flat':
            flat_prices[module_name] = float(mod["UnitPrice"]) if pd.notna(mod["UnitPrice"]) else 0.0
        elif pricing_type == 'tiered':
            tier_configs[module_name] = tiers_df[tiers_df["Module"] == module_name].copy()

# ✅ Save updates into session_state
if admin_mode and st.sidebar.button("💾 Save Usage Settings"):
    new_df = modules_df.copy()
    for mod_name, default_val, max_val in updated_usage_settings:
        new_df.loc[new_df["Module"] == mod_name, "DefaultUsage"] = default_val
        new_df.loc[new_df["Module"] == mod_name, "MaxUsage"] = max_val
    st.session_state[CONFIG_KEY] = new_df
    st.success("✅ Usage settings saved to session.")

    if st.sidebar.checkbox("💾 Permanently overwrite CSV file"):
        new_df.to_csv(DEFAULT_CONFIG, index=False)
        st.sidebar.success("✅ File overwritten on disk.")

# ===== CALCULATION & DISPLAY =====
records = []
for module_name, usage in usage_inputs.items():
    pricing_type = str(modules_df[modules_df["Module"] == module_name]["Type"].values[0]).lower()
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
                    thresh = float(t["Threshold"])
                    price = float(t["Price"])
                    finite.append((thresh, price))
                except:
                    infinite_price = float(t["Price"])
            finite.sort()
            remaining = usage
            prev = 0
            for thresh, price in finite:
                if remaining <= 0: break
                span = thresh - prev
                portion = min(span, remaining)
                cost += portion * price
                unit_price = price
                remaining -= portion
                prev = thresh
            if remaining > 0:
                fallback = infinite_price if infinite_price is not None else finite[-1][1] if finite else 0.0
                cost += remaining * fallback
                unit_price = fallback

    records.append({
        "Module": module_name,
        "Category": category,
        "Usage": usage,
        "Pricing Type": pricing_type,
        "Unit Price (used)": unit_price,
        "Cost (FCFA)": cost
    })

results_df = pd.DataFrame(records)
total_cost = results_df["Cost (FCFA)"].sum()

# ===== UI OUTPUTS =====
st.subheader(f"💰 {'Estimated Monthly Cost' if not is_french else 'Coût Mensuel Estimé'}: {total_cost:,.0f} FCFA")

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### 📊 Bar Chart: Cost per Module" if not is_french else "#### 📊 Coût par Module")
    st.bar_chart(results_df.set_index("Module")["Cost (FCFA)"])
with col2:
    st.markdown("#### 🥧 Pie Chart: Cost by Category" if not is_french else "#### 🥧 Coût par Catégorie")
    category_summary = results_df.groupby("Category", as_index=False)["Cost (FCFA)"].sum()
    pie = alt.Chart(category_summary).mark_arc(innerRadius=40).encode(
        theta=alt.Theta("Cost (FCFA)", type="quantitative"),
        color=alt.Color("Category", type="nominal"),
        tooltip=["Category", "Cost (FCFA)"]
    )
    st.altair_chart(pie, use_container_width=True)

st.markdown("### 🧾 Cost Breakdown by Module" if not is_french else "### 🧾 Détail du Coût par Module")
st.dataframe(results_df.style.format({col: "{:,.0f}" for col in results_df.select_dtypes(include="number").columns}))

# ✅ Export updated config
csv_data = st.session_state[CONFIG_KEY].to_csv(index=False)
st.download_button("⬇️ Download Current Config CSV", csv_data, file_name="updated_modules_config.csv", mime="text/csv")
