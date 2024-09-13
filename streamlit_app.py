import streamlit as st
import requests
import json

BASE_URL = st.secrets["BASE_URL"]


def send_request(endpoint, data):
    response = requests.post(f"{BASE_URL}/{endpoint}", json=data)
    return response.json()


st.title("SaileBot Demo")

# Initialize session state variables
if 'step' not in st.session_state:
    st.session_state.step = 'start'
if 'account_id' not in st.session_state:
    st.session_state.account_id = None
if 'contact_id' not in st.session_state:
    st.session_state.contact_id = None
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None

# Step 1: Find similar accounts
if st.session_state.step == 'start':
    st.header("Find Similar Accounts")
    company_name = st.text_input("Enter a company name to find similar accounts:")
    if st.button("Find Similar Accounts"):
        response = send_request("sailebot_flow", {"company_name": company_name})
        print(response)
        st.write(response["message"])
        st.session_state.similar_accounts = response["similar_accounts"]
        st.session_state.step = 'select_account'

# Step 2: Select and add an account
elif st.session_state.step == 'select_account':
    st.header("Select an Account")
    selected_account = st.selectbox("Select an account to add:",
                                    [acc["id"] for acc in st.session_state.similar_accounts])
    if st.button("Add Account"):
        response = send_request("add_account", {"account_id": selected_account})
        print(response)
        st.write(response["message"])
        st.session_state.account_id = response["account_id"]
        st.session_state.step = 'find_contacts'

# Step 3: Find contacts
elif st.session_state.step == 'find_contacts':
    st.header("Find Contacts")
    if st.button("Find Contacts"):
        response = send_request("find_contacts", {"account_id": st.session_state.account_id})
        st.write(response["message"])
        st.session_state.contacts = response["contacts"]
        st.session_state.step = 'select_contact'

# Step 4: Select a contact and generate email
elif st.session_state.step == 'select_contact':
    st.header("Select a Contact and Generate Email")
    selected_contact = st.selectbox("Select a contact:",
                                    [contact["id"] for contact in st.session_state.contacts])
    if st.button("Generate Email"):
        response = send_request("generate_email", {
            "salesperson_id": "222476",  # You might want to make this dynamic
            "contact_id": selected_contact,
            "account_id": st.session_state.account_id
        })
        print(response)
        st.session_state.email_content = response["email_content"]
        st.session_state.thread_id = response["thread_id"]
        st.session_state.contact_id = selected_contact
        st.session_state.step = 'review_email'

# Step 5: Review and refine email
elif st.session_state.step == 'review_email':
    st.header("Review and Refine Email")
    st.write("Generated Email:")
    st.markdown(st.session_state.email_content)
    
    action = st.radio("What would you like to do?", ["Approve", "Refine", "Cancel"])
    
    if action == "Approve":
        if st.button("Finalize Email"):
            response = send_request("finalize_email", {
                "thread_id": st.session_state.thread_id,
                "contact_id": st.session_state.contact_id
            })
            st.write(response["message"])
            st.session_state.step = 'start'  # Reset to start
    elif action == "Refine":
        feedback = st.text_area("Provide feedback for refinement:")
        if st.button("Submit Feedback"):
            response = send_request("refine_email", {
                "salesperson_id": "SAL001",  # You might want to make this dynamic
                "contact_id": st.session_state.contact_id,
                "account_id": st.session_state.account_id,
                "feedback": feedback,
                "thread_id": st.session_state.thread_id  # Include the thread_id
            })
            st.session_state.email_content = response["email_content"]
            st.session_state.thread_id = response["thread_id"]
            st.experimental_rerun()
    elif action == "Cancel":
        if st.button("Cancel and Start Over"):
            st.session_state.step = 'start'  # Reset to start
            st.experimental_rerun()

# Add a sidebar to show the current step
st.sidebar.header("Current Step")
st.sidebar.write(st.session_state.step.replace('_', ' ').title())

# Add a button to reset the entire process
if st.sidebar.button("Start Over"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

