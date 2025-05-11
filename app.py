import streamlit as st
import mysql.connector

# TiDB Connection config
config = {
    'host': 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com',
    'user': '2DBRzF53CL7KjpF.root',
    'password': '4MmFoKuRZJLpzuBQ',
    'database': 'STUDENT_PAYMENT_TRACKER',
    'ssl_ca': 'isrgrootx1.pem'  # Place the PEM file in the same folder as this script
}

st.set_page_config(page_title="Student Portal", layout="wide")
st.sidebar.title("Menu")
page = st.sidebar.radio("Go to", ["Add Student", "Submit Fees"])

def insert_student(fname, lname, phone, sclass, school_id):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        query = """
            INSERT INTO STUDENT_DETAILS 
            (S_F_NAME, S_L_NAME, S_PH_NUM, S_CLASS, S_SCHL_ID)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (fname, lname, phone, sclass, int(school_id)))
        conn.commit()
        st.success("Student added successfully!")
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if page == "Add Student":
    st.header("Add Student Details")

    with st.form("student_form"):
        col1, col2 = st.columns(2)
        fname = col1.text_input("First Name")
        lname = col2.text_input("Last Name")
        phone = st.text_input("Phone Number")
        sclass = st.text_input("Class")
        school_id = st.text_input("School ID")
        submitted = st.form_submit_button("Submit")

        if submitted:
            if fname and lname and phone and sclass and school_id:
                insert_student(fname, lname, phone, sclass, school_id)
            else:
                st.warning("Please fill all fields.")

elif page == "Submit Fees":
    st.header("Submit Fees")
    st.write("This section is under development.")
