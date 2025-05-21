import streamlit as st
import pandas as pd
import altair as alt

# Load data
modules_df = pd.read_csv('modules_config_clean.csv')
tiers_df = pd.read_csv('module_tiers_clean.csv')

# Page config
st.set_page_config(page_title='Transport Pricing Simulator', layout='wide')

# App title and total cost placeholder
st.title("🚌 Transport Pricing Simulator")
total_cost_placeholder = st.empty()

# Admin toggle in sidebar
st.sidebar.header("Settings")
admin_mode = st.sidebar.checkbox("Enable Admin Mode")

# Column Names
module_col = 'Module'
type_col = 'Type'
price_col = 'UnitPrice'
tier_module_col = 'Module'
tier_threshold_col = 'Threshold'
tier_price_col = 'Price'

usage_inputs = {}
flat_prices = {}
tier_configs = {}

# Sidebar for module usage and admin config
st.sidebar.subheader("📊 Module Usage")
for _, mod in modules_df.iterrows():
    module_name = str(mod[module_col])
    pricing_type = str(mod[type_col]).strip().lower()

    usage = st.sidebar.slider(f"{module_name}", 0, 1000, 0)
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

# Cost calculation
results = []
for module_name, usage in usage_inputs.items():
    pricing_type = str(modules_df[modules_df[module_col] == module_name][type_col].values[0]).lower()
    cost = 0.0

    if pricing_type == 'flat':
        cost = usage * flat_prices.get(module_name, 0.0)
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
                    infinite_price = float(t[tier_price_col])
            finite.sort()
            remaining = usage
            prev = 0
            for thresh, price in finite:
                if remaining <= 0: break
                span = thresh - prev
                portion = min(span, remaining)
                cost += portion * price
                remaining -= portion
                prev = thresh
            if remaining > 0:
                cost += remaining * (infinite_price if infinite_price is not None else finite[-1][1] if finite else 0.0)

    results.append({"Module": module_name, "Usage": usage, "Cost": cost})

# Display total cost at top
results_df = pd.DataFrame(results)
total = results_df["Cost"].sum()
total_cost_placeholder.subheader(f"💰 Estimated Monthly Cost: {total:,.0f} FCFA")

# Visual breakdown
col1, col2 = st.columns(2)
with col1:
    st.subheader("Cost per Module")
    st.bar_chart(results_df.set_index("Module")["Cost"])
with col2:
    st.subheader("Cost Distribution")
    pie = alt.Chart(results_df).mark_arc(innerRadius=40).encode(
        theta=alt.Theta("Cost", type="quantitative"),
        color=alt.Color("Module", type="nominal"),
        tooltip=["Module", "Cost"]
    )
    st.altair_chart(pie, use_container_width=True)

# Download
st.download_button("📥 Download Cost Breakdown", results_df.to_csv(index=False), file_name="pricing_breakdown.csv", mime="text/csv")
