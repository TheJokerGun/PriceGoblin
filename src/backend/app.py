# app.py

import streamlit as st
from database import SessionLocal, init_db, User, Product
from sqlalchemy.orm import Session

init_db()

st.set_page_config(page_title="PriceGoblin Test UI")

st.title("🧌 PriceGoblin Backend Test UI")

# -------------------
# LOGIN SECTION
# -------------------

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    email = st.text_input("Enter your Teams / Outlook Email")

    if st.button("Login"):
        if email:
            db: Session = SessionLocal()

            user = db.query(User).filter(User.email == email).first()

            if not user:
                user = User(email=email)
                db.add(user)
                db.commit()
                db.refresh(user)

            st.session_state.user = user
            st.success(f"Logged in as {user.email}")
            db.close()
            st.rerun()
        else:
            st.warning("Please enter an email.")

else:
    st.sidebar.success(f"Logged in: {st.session_state.user.email}")

    option = st.sidebar.radio(
        "Choose tracking type",
        ["URL", "Category"]
    )

    db: Session = SessionLocal()

    if option == "URL":
        st.header("Track via URL")

        url = st.text_input("Enter Product URL")
        name = st.text_input("Optional Product Name")

        if st.button("Add Product"):
            product = Product(
                name=name,
                url=url,
                category=None,
                user_id=st.session_state.user.id
            )
            db.add(product)
            db.commit()
            st.success("Product added via URL.")

    elif option == "Category":
        st.header("Track via Category")

        category = st.selectbox(
            "Select Category",
            ["General", "Games", "Cards"]
        )

        name = st.text_input("Enter Product Name")

        if st.button("Add Product"):
            product = Product(
                name=name,
                url=None,
                category=category,
                user_id=st.session_state.user.id
            )
            db.add(product)
            db.commit()
            st.success("Product added via Category.")

    # Show user products
    st.subheader("Your Tracked Products")

    products = db.query(Product).filter(
        Product.user_id == st.session_state.user.id
    ).all()

    for p in products:
        st.write(f"• {p.name or 'Unnamed'} | {p.category or p.url}")

    db.close()
