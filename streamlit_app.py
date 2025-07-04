import streamlit as st
import pandas as pd
from io import BytesIO
import streamlit as st
import pandas as pd
from io import BytesIO

# ✅ Create a dynamic sample file
sample_erp = pd.DataFrame({
    'ERP_ID': [1, 1, 2],
    'SKU': ['SKU1', 'SKU2', 'SKU3'],
    'Qty': [10, 20, 30]
})

sample_inventory = pd.DataFrame({
    'SKU': ['SKU1', 'SKU2', 'SKU3'],
    'Qty': [15, 25, 35]
})

# ✅ Write to Excel in memory
output = BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    sample_erp.to_excel(writer, index=False, sheet_name='ERP')
    sample_inventory.to_excel(writer, index=False, sheet_name='Inventory')
data = output.getvalue()

# ✅ Streamlit download button
st.download_button(
    label="⬇️ Download Sample Format",
    data=data,
    file_name="Sample_Format.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def allocate_stock(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    erp_df = xls.parse("ERP")
    inventory_df = xls.parse("Inventory")

    erp_df['SKU'] = erp_df['SKU'].astype(str)
    inventory_df['SKU'] = inventory_df['SKU'].astype(str)

    erp_df = erp_df.rename(columns={'Qty': 'ERP_Qty'})
    inventory_df = inventory_df.rename(columns={'Qty': 'Inventory_Qty'})
    erp_df['Allocated_Qty'] = 0
    inventory_dict = inventory_df.set_index('SKU')['Inventory_Qty'].to_dict()

    # 👉 Change 'ERP' below if your order column has a different name
    erp_group = erp_df.groupby('ERP_ID')

    for erp_id, group in erp_group:
        can_allocate = True
        for _, row in group.iterrows():
            sku = row['SKU']
            demand = row['ERP_Qty']
            available = inventory_dict.get(sku, 0)
            if available < demand:
                can_allocate = False
                break

        if can_allocate:
            for idx, row in group.iterrows():
                sku = row['SKU']
                demand = row['ERP_Qty']
                erp_df.at[idx, 'Allocated_Qty'] = demand
                inventory_dict[sku] -= demand

    # Save result to in-memory Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        erp_df.to_excel(writer, sheet_name='Result', index=False)
        pd.DataFrame(inventory_dict.items(), columns=['SKU', 'Remaining_Qty']).to_excel(writer, sheet_name='Remaining Inventory', index=False)
    output.seek(0)
    return output

# ✅ Streamlit UI
st.title("Orchids Exchange Stock Allocation By ERP")
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
if uploaded_file:
    # ✅ Show sheet names
    xls = pd.ExcelFile(uploaded_file)
    st.write("### Sheets in uploaded Excel:", xls.sheet_names)

    # ✅ Let user pick a sheet to preview (optional)
    sheet_to_preview = st.selectbox("Select a sheet to preview", xls.sheet_names)

    # ✅ Read and show a sample of the sheet
    df_preview = pd.read_excel(uploaded_file, sheet_name=sheet_to_preview)
    st.write("### Preview of selected sheet")
    st.dataframe(df_preview.head())  # show first 5 rows

if uploaded_file:
    if st.button("Run Allocation"):
        result = allocate_stock(uploaded_file)
        st.success("✅ Allocation complete!")
        st.download_button("📥 Download Result Excel", result, file_name="Allocated_Result.xlsx")
