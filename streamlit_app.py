# Import python packages
import tempfile
import time
import requests
import streamlit as st
from snowflake.snowpark.functions import col

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write(
    """Choose the fruits you want in your custom Smoothie!
    """
)

name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your smoothie is", name_on_order)

# Write the private key from Streamlit Secrets to a temporary file
with tempfile.NamedTemporaryFile(delete=False, suffix=".p8") as tmp_key:
    tmp_key.write(st.secrets["snowflake_key"]["private_key"].encode("utf-8"))
    key_path = tmp_key.name

cnx = st.connection("snowflake", private_key_file=key_path)
session = cnx.session()

# Pull both FRUIT_NAME and SEARCH_ON from Snowflake
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Convert the Snowpark Dataframe to a Pandas Dataframe so we can use the LOC function
pd_df = my_dataframe.to_pandas()

ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe,
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.subheader(fruit_chosen + ' Nutrition Information')

        try:
            url = "https://" + f"://smoothiefroot.com{search_on}"
            smoothiefroot_response = requests.get(url)
            sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
            time.sleep(0.2)
        except Exception:
            st.warning(f"Nutrition data unavailable for {fruit_chosen}")

    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES ('{ingredients_string}', '{name_on_order}')
    """

    st.write(my_insert_stmt)
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
