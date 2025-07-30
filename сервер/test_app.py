import streamlit as st

st.title("🧪 Тест сервера")
st.write("Если вы видите это сообщение - сервер работает!")
st.success("✅ Streamlit запущен успешно!")

if st.button("Тест кнопки"):
    st.balloons()
    st.write("🎉 Всё работает!")
