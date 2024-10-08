import streamlit as st
import requests
import json
import time

BASE_URL = st.secrets["BASE_URL"]


st.title("Personalized Email Generation Demo")

def send_request(endpoint, data):
    response = requests.post(f"{BASE_URL}/{endpoint}", json=data)
    print(f"Debug - {endpoint} response: {response.json()}")  # Debug print
    return response.json()


if 'step' not in st.session_state:
    st.session_state.step = 'start'
if 'account_id' not in st.session_state:
    st.session_state.account_id = None
if 'contact_id' not in st.session_state:
    st.session_state.contact_id = None
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None
if 'response' not in st.session_state:
    st.session_state.response = None
if 'email_content' not in st.session_state:
    st.session_state.email_content = None
if 'refined_email' not in st.session_state:
    st.session_state.refined_email = None

# Display current response and email content
if st.session_state.response:
    st.write(st.session_state.response)
    st.session_state.response = None  # Clear the response after displaying

if st.session_state.refined_email:
    st.write("Current Refined Email Content:")
    st.markdown(st.session_state.refined_email)

elif st.session_state.email_content:
    st.write("Current Email Content:")
    st.markdown(st.session_state.email_content)

# Step 1: Find similar accounts
if st.session_state.step == 'start':
    st.header("Find Similar Accounts")
    company_name = st.text_input("Enter a company name to find similar accounts:")
    if st.button("Find Similar Accounts"):
        with st.spinner("Finding similar accounts..."):
            response = send_request("sailebot_flow", {"company_name": company_name})
            time.sleep(2)
        st.session_state.response = response["message"]
        st.session_state.similar_accounts = response.get("similar_accounts", [])
        print(f"Debug - Similar accounts: {st.session_state.similar_accounts}")  # Debug print
        st.session_state.step = 'select_account'
        st.rerun()

# Step 2: Select and add an account
elif st.session_state.step == 'select_account':
    st.header("Select an Account")
    if st.session_state.similar_accounts:
        accounts = st.session_state.similar_accounts
        account_display = [account["name"] for account in accounts]
        account_ids = [account["id"] for account in accounts]
        
        selected_account = st.selectbox("Select an Account", options=account_display)
        selected_account_id = account_ids[account_display.index(selected_account)]
        print(f"selected_account_id {selected_account_id}")
        if st.button("Add Account"):
            with st.spinner("Adding account..."):
                response = send_request("add_account", {"account_id": selected_account_id})
                time.sleep(1)
            st.session_state.response = response["message"]
            st.session_state.account_id = response.get("account_id")
            print(f"Debug - Added account: {st.session_state.account_id}")  # Debug print
            st.session_state.step = 'find_contacts'
            st.rerun()
    else:
        st.write("No similar accounts found. Please go back and try again.")

# Step 3: Find contacts
elif st.session_state.step == 'find_contacts':
    st.header("Find Contacts")
    if st.button("Find Contacts"):
        with st.spinner("Finding contacts..."):
            response = send_request("find_contacts", {"account_id": st.session_state.account_id})
            time.sleep(2)
        st.session_state.response = response["message"]
        st.session_state.contacts = response.get("contacts", [])
        print(f"Debug - Contacts found: {st.session_state.contacts}")  # Debug print
        st.session_state.step = 'select_contact'
        st.rerun()

# Step 4: Select a contact and generate email
elif st.session_state.step == 'select_contact':
    st.header("Select a Contact and Generate Email")
    if st.session_state.contacts:
        selected_contacts = [f"{con['name']} - {con['title']}" for con in st.session_state.contacts]
        selected_contact_ids = [con["id"] for con in st.session_state.contacts]
        
        selected_contact_whole = st.selectbox("Select a Contact", options=selected_contacts)
        selected_contact = selected_contact_ids[selected_contacts.index(selected_contact_whole)]
        
        if st.button("Generate Email"):
            with st.spinner("Generating Email..."):
                response = send_request("generate_email", {
                    "salesperson_id": "222476",  # You might want to make this dynamic
                    "contact_id": selected_contact,
                    "account_id": st.session_state.account_id
                })
            if 'email_content' in response and 'thread_id' in response:
                st.session_state.email_content = response["email_content"]
                st.session_state.thread_id = response["thread_id"]
                st.session_state.contact_id = selected_contact
                st.session_state.step = 'review_email'
                st.rerun()
            else:
                st.error(f"Error generating email: {response.get('detail', 'Unknown error')}")
    else:
        st.write("No contacts found. Please go back and try again.")

# Step 5: Review and refine email
elif st.session_state.step == 'review_email':
    st.header("Review and Refine Email")
    
    if st.session_state.email_content:
        st.write("Generated Email:")
        st.markdown(st.session_state.email_content)
    else:
        st.error("No email content available. Please go back and generate an email.")
        st.session_state.step = 'select_contact'
        st.rerun()

    action = st.radio("What would you like to do?", ["Approve", "Refine", "Cancel"])
    
    if action == "Approve":
        if st.button("Finalize Email"):
            if st.session_state.thread_id and st.session_state.contact_id:
                with st.spinner("Finalizing email..."):
                    response = send_request("finalize_email", {
                        "thread_id": st.session_state.thread_id,
                        "contact_id": st.session_state.contact_id
                    })
                    time.sleep(3)
                if 'message' in response:
                    st.success(response["message"])
                    if 'email_preview' in response:
                        st.write("Email Preview:")
                        st.write(response["email_preview"])
                    if 'celebration' in response:
                        st.balloons()
                        st.success(response["celebration"])
                    
                    # Add a button to start a new email
                    if st.button("Start New Email"):
                        # Reset necessary session state variables
                        for key in ['email_content', 'thread_id', 'contact_id', 'account_id']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.session_state.step = 'start'
                        st.rerun()
                else:
                    st.error(f"Error finalizing email: {response.get('detail', 'Unknown error')}")
            else:
                st.error("Missing thread_id or contact_id. Cannot finalize email.")


    elif action == "Refine":
        feedback = st.text_area("Provide feedback for refinement:")
        if st.button("Submit Feedback"):
            if st.session_state.thread_id:
                with st.spinner("Refining email..."):
                    response = send_request("refine_email", {
                        "salesperson_id": "222476",  # You might want to make this dynamic
                        "contact_id": st.session_state.contact_id,
                        "account_id": st.session_state.account_id,
                        "feedback": feedback,
                        "thread_id": st.session_state.thread_id
                    })
                if 'email_content' in response:
                    st.session_state.email_content = response["email_content"]
                    st.success("Email refined successfully!")
                    st.rerun()
                else:
                    st.error(f"Error refining email: {response.get('detail', 'Unknown error')}")
            else:
                st.error("Missing thread_id. Cannot refine email.")

    elif action == "Cancel":
        if st.button("Cancel and Start Over"):
            for key in ['email_content', 'thread_id', 'contact_id', 'account_id']:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.step = 'start'
            st.rerun()

# Add a sidebar to show the current step
st.sidebar.header("Current Step")
st.sidebar.write(st.session_state.step.replace('_', ' ').title())

# Add a button to reset the entire process
if st.sidebar.button("Start Over"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# Debug print of current session state
print(f"Debug - Current session state: {st.session_state}")


st.sidebar.write("Debug Info:")
st.sidebar.write(f"Current Step: {st.session_state.step}")
st.sidebar.write(f"Thread ID: {st.session_state.get('thread_id', 'Not set')}")
st.sidebar.write(f"Contact ID: {st.session_state.get('contact_id', 'Not set')}")
st.sidebar.write(f"Account ID: {st.session_state.get('account_id', 'Not set')}")