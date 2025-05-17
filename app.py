import streamlit as st
from streamlit_option_menu import option_menu
import mysql.connector
from datetime import date
import pandas as pd
st.set_page_config(page_title="Student Portal", layout="wide")
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css("styles.css")
# --- DB Configuration ---
config = {
    'host': 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com',
    'user': '2DBRzF53CL7KjpF.root',
    'password': '4MmFoKuRZJLpzuBQ',
    'database': 'STUDENT_PAYMENT_TRACKER',
    'ssl_ca': 'isrgrootx1.pem',
    'ssl_verify_cert': True
}

# --- Page Setup ---

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "Welcome"

with st.sidebar:
    selected = option_menu(
        "Main Menu",
        [
            "Welcome",  # default/initial screen
            "Add Student",
            "Add School Details",
            "Add Subject Details",
            "Set Class Wise Fees",
            "Submit Fees",
            "View Student",
            "View Month Wise Due Fees",
            "View Payment History"
        ],
        icons=[
            "house", "person-plus", "building", "book", "cash-coin",
            "credit-card", "people", "calendar-x", "file-earmark-text"
        ],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#9fb6c3"},
            "icon": {"color": "#003366", "font-size": "16px"},
            "box-shadow": "none",         # Removes shadow
                "border": "none",             # Removes border
                "border-radius": "0px" ,
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px"},
            "nav-link-selected": {"background-color": "#ed7e10", "color": "white"},
        }
    )

# Store selection in session state
st.session_state.page = selected
#page = st.session_state.page



# --- DB Functions ---


def insert_student(fname, lname, phone, sclass, school_id, subject_id):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(S_ID) FROM STUDENT_DETAILS")
        next_s_id = (cursor.fetchone()[0] or 0) + 1
        cursor.execute("""
            INSERT INTO STUDENT_DETAILS (S_ID, S_F_NAME, S_L_NAME, S_PH_NUM, S_CLASS, S_SCHL_ID, SUB_ID)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (next_s_id, fname, lname, phone, sclass, int(school_id), int(subject_id)))
        conn.commit()
        st.success(f"Student added successfully with ID: {next_s_id}")
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def add_school_details(name):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(SCHL_ID) FROM SCHOOL_DETAILS")
        next_id = (cursor.fetchone()[0] or 0) + 1
        cursor.execute("INSERT INTO SCHOOL_DETAILS (SCHL_ID, SCHL_NAME) VALUES (%s, %s)", (next_id, name))
        conn.commit()
        st.success("School added successfully!")
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def add_subject_details(name):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(SUB_ID) FROM SUBJECT")
        next_id = (cursor.fetchone()[0] or 0) + 1
        cursor.execute("INSERT INTO SUBJECT (SUB_ID, SUB_NAME) VALUES (%s, %s)", (next_id, name))
        conn.commit()
        st.success("Subject added successfully!")
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def set_fees_by_class(clas, fees, subject_id):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO FEES (S_CLASS, FEES,SUB_ID) VALUES (%s, %s,%s)
            ON DUPLICATE KEY UPDATE FEES = VALUES(FEES)
        """, (clas, int(fees), int(subject_id)))
        conn.commit()
        st.success("Fees added/updated successfully!")
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def fetch_students_by_class(class_id):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT S_ID, CONCAT(S_F_NAME, ' ', S_L_NAME) AS Name, S_PH_NUM,
                   SCHD.SCHL_NAME, SUB.SUB_NAME
            FROM STUDENT_DETAILS STDS
            LEFT JOIN SCHOOL_DETAILS SCHD ON STDS.S_SCHL_ID = SCHD.SCHL_ID
            LEFT JOIN SUBJECT SUB ON STDS.SUB_ID = SUB.SUB_ID
            WHERE STDS.S_CLASS = %s
        """, (class_id,))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def submit_fees_to_capture_table(s_id, name, phone, year, month, payment_date, mode, receipt_sent):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO STUDENT_FEES_CAPTURED
            (S_ID, S_NAME, S_PH_NUM, FEES_PAID_FOR_YEAR, FEES_PAID_FOR_MONTH, FEES_PAID_ON, FEES_PAID_MODE, RECEIPT_SENT)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (s_id, name, phone, year, month, payment_date, mode, receipt_sent))
        conn.commit()
        st.success("✅ Fee payment recorded successfully.")
    except mysql.connector.Error as err:
        st.error(f"❌ Database Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
def get_due_fees_students(month, year):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT SD.S_ID, SD.S_F_NAME, SD.S_L_NAME, SD.S_PH_NUM
            FROM STUDENT_DETAILS SD
            LEFT JOIN STUDENT_FEES_CAPTURED FC
              ON SD.S_ID = FC.S_ID
              AND FC.FEES_PAID_FOR_MONTH = %s
              AND FC.FEES_PAID_FOR_YEAR = %s
            WHERE FC.S_ID IS NULL
        """
        cursor.execute(query, (month, year))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
def get_payment_history_by_name(full_name):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
              SD.S_ID,
              CONCAT(SD.S_F_NAME, ' ', SD.S_L_NAME) AS STUDENT_NAME,
              SD.S_PH_NUM,
              FC.FEES_PAID_FOR_MONTH,
              FC.FEES_PAID_FOR_YEAR,
              FC.FEES_PAID_ON,
              FC.FEES_PAID_MODE,
              FC.RECEIPT_SENT
            FROM STUDENT_DETAILS SD
            INNER JOIN STUDENT_FEES_CAPTURED FC
              ON SD.S_ID = FC.S_ID
            WHERE CONCAT(SD.S_F_NAME, ' ', SD.S_L_NAME) = %s
            ORDER BY FC.FEES_PAID_FOR_YEAR, FC.FEES_PAID_FOR_MONTH
        """
        cursor.execute(query, (full_name,))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# --- Pages ---
page = st.session_state.page
# Add Student
if page == "Welcome":
    st.title("👋 Welcome to Jeet's Computer Batch!!")
    st.markdown("""
        Please use the sidebar to navigate through the system.\n
        Contact Me at **+91 8334039125** for any queries.
    """)
elif page == "Add Student":
    st.header("Add Student Details")
    with st.form("student_form"):
        col1, col2 = st.columns(2)
        fname = col1.text_input("First Name")
        lname = col2.text_input("Last Name")
        phone = st.text_input("Phone Number")
        sclass = st.text_input("Class")

        try:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT SCHL_ID, SCHL_NAME FROM SCHOOL_DETAILS")
            schools = cursor.fetchall()
            school_options = {s["SCHL_NAME"]: s["SCHL_ID"] for s in schools}
            selected_school = st.selectbox("Select School", list(school_options.keys()))
            school_id = school_options[selected_school]

            cursor.execute("SELECT SUB_ID, SUB_NAME FROM SUBJECT")
            subs = cursor.fetchall()
            sub_options = {s["SUB_NAME"]: s["SUB_ID"] for s in subs}
            selected_subject = st.selectbox("Select Subject", list(sub_options.keys()))
            subject_id = sub_options[selected_subject]
        except mysql.connector.Error as err:
            st.error(f"Database Error: {err}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

        submitted = st.form_submit_button("Submit")
        if submitted and fname and lname and phone and sclass:
            insert_student(fname, lname, phone, sclass, school_id, subject_id)
        elif submitted:
            st.warning("Please fill all fields.")

# Add School
elif page == "Add School Details":
    st.header("Add School")
    with st.form("school_form"):
        name = st.text_input("School Name")
        if st.form_submit_button("Submit"):
            if name:
                add_school_details(name)
            else:
                st.warning("Please enter a school name.")

# Add Subject
elif page == "Add Subject Details":
    st.header("Add Subject")
    with st.form("subject_form"):
        name = st.text_input("Subject Name")
        if st.form_submit_button("Submit"):
            if name:
                add_subject_details(name)
            else:
                st.warning("Please enter a subject name.")

# Set Class Fees
elif page == "Set Class Wise Fees":
    st.header("Set Class-wise Fees")
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT SUB_ID,SUB_NAME FROM SUBJECT")
    subs = cursor.fetchall()
    sub_options = {s["SUB_NAME"]: s["SUB_ID"] for s in subs}
    selected_subject = st.selectbox("Select Subject", list(sub_options.keys()))
    subject_id = sub_options[selected_subject]
    with st.form("fees_form"):
        clas = st.text_input("Class")
        fees = st.text_input("Fees")
        if st.form_submit_button("Submit"):
            if clas and fees:
                set_fees_by_class(clas, fees,subject_id)
            else:
                st.warning("Please fill all fields.")

# Submit Fees
elif page == "Submit Fees":
    st.header("Submit Fees")

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
        SELECT S_ID,CONCAT(S_F_NAME, ' ', S_L_NAME) AS Name, S_PH_NUM,SCHD.SCHL_NAME,SUB.SUB_NAME,FEES.FEES,STDS.S_CLASS         
        FROM STUDENT_DETAILS STDS LEFT JOIN SCHOOL_DETAILS SCHD ON STDS.S_SCHL_ID=SCHD.SCHL_ID
        LEFT JOIN SUBJECT SUB ON STDS.SUB_ID=SUB.SUB_ID
        LEFT JOIN FEES ON STDS.S_CLASS=FEES.S_CLASS
                       """)
        
        students = cursor.fetchall()
        student_options = {s["Name"]: s["S_ID"] for s in students}
        selected_name = st.selectbox("Select Student", list(student_options.keys()))
        selected_id = student_options[selected_name]

        cursor.execute("""
            SELECT STDS.S_ID, STDS.S_F_NAME, STDS.S_L_NAME, STDS.S_PH_NUM,
                STDS.S_CLASS, SCHD.SCHL_NAME, SUB.SUB_NAME, FEES.FEES
            FROM STUDENT_DETAILS STDS
            LEFT JOIN SCHOOL_DETAILS SCHD ON STDS.S_SCHL_ID = SCHD.SCHL_ID
            LEFT JOIN SUBJECT SUB ON STDS.SUB_ID = SUB.SUB_ID
            LEFT JOIN FEES ON STDS.S_CLASS = FEES.S_CLASS
            WHERE STDS.S_ID = %s
            """, (selected_id,))
        #student = cursor.fetchone()
        student = cursor.fetchone()
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
        student = None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    if student:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Personal Details")
            st.write(f"**ID:** {student['S_ID']}")
            st.write(f"**Name:** {student['S_F_NAME']} {student['S_L_NAME']}")
            st.write(f"**Phone:** {student['S_PH_NUM']}")
            st.write(f"**Class:** {student['S_CLASS']}")
            
        with col2:
            st.subheader("School and Subject Details")
            st.write(f"**School:** {student['SCHL_NAME']}")
            st.write(f"**Subject:** {student['SUB_NAME']}")
            st.write(f"**Fees:** ₹{student['FEES']}")
        with st.form("submit_fees_form"):
            col1, col2 = st.columns(2)

            with col1:
                year = st.selectbox("Fees Paid For(Year)", ["2024", "2025", "2026"])
                fee_amount = st.number_input("Enter Fee Amount to Pay", min_value=0, value=0)
                payment_date = st.date_input("Payment Date", value=date.today())
            
            with col2:
                month = st.selectbox("Fees Paid For(Month)", [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ])
                mode = st.selectbox("Payment Mode", ["Cash", "Card", "Online", "UPI"])
                receipt_sent = st.selectbox("Receipt Sent", ["Yes", "No"])
            if st.form_submit_button("Submit Payment"):
                full_name = f"{student['S_F_NAME']} {student['S_L_NAME']}"
                submit_fees_to_capture_table(
                    student['S_ID'], full_name, student['S_PH_NUM'],
                    year, month, payment_date, mode, receipt_sent
                )

# View Students
elif page == "View Student":
    st.header("View Students by Class")
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT S_CLASS FROM STUDENT_DETAILS")
        classes = cursor.fetchall()
        class_options = [c["S_CLASS"] for c in classes]
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
        class_options = []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    selected_class = st.selectbox("Select Class", class_options)
    if st.button("Search"):
        students = fetch_students_by_class(selected_class)
        if students:
            df = pd.DataFrame(students)
            st.dataframe(df)
        else:
            st.info("No students found.")
elif page == "View Month Wise Due Fees":
    st.header("View Month-Wise Due Fees")

    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("Select Year", ["2024", "2025", "2026"])
    with col2:
        selected_month = st.selectbox("Select Month", [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])

    if st.button("Show Due Students"):
        due_students = get_due_fees_students(selected_month, selected_year)
        if due_students:
            df = pd.DataFrame(due_students)
            df.columns = ["ID", "First Name", "Last Name", "Phone Number"]
            st.dataframe(df)
        else:
            st.info("🎉 All students have paid fees for the selected month and year.")
elif page == "View Payment History":
    st.header("View Student Payment History")

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT CONCAT(S_F_NAME, ' ', S_L_NAME) AS full_name FROM STUDENT_DETAILS")
        student_names = [row['full_name'] for row in cursor.fetchall()]
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
        student_names = []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    if student_names:
        selected_student = st.selectbox("Select Student", student_names)

        if st.button("Show Payment History"):
            history = get_payment_history_by_name(selected_student)
            if history:
                df = pd.DataFrame(history)
                df.columns = ["ID", "Name", "Phone", "Fees Paid For - Month", "Fees Paid For - Year", "Paid On", "Mode", "Receipt Sent"]
                st.dataframe(df)
            else:
                st.info("No payment history found for this student.")
    else:
        st.warning("No student records found.")
