import streamlit as st
import requests
from typing import Dict, Any
import json


# API_BASE_URL = "http://localhost:8000"
API_BASE_URL = "https://utkarsh134-fastapi-hackathonin2mins.hf.space"

def init_session_state():
    if 'context' not in st.session_state:
        st.session_state.context = None
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'registration_complete' not in st.session_state:
        st.session_state.registration_complete = False
    if 'started' not in st.session_state:
        st.session_state.started = False
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None

def send_message(message: str) -> Dict[str, Any]:
    try:
        payload = {
            "session_id": st.session_state.session_id,
            "message": message,
            "context": st.session_state.context,
            "current_question": st.session_state.current_question
        }
        
        print(f"Sending request: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload
        )
        response.raise_for_status()
        
        response_data = response.json()
        print(f"Received response: {json.dumps(response_data, indent=2)}")
        
        return response_data
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with the server: {str(e)}")
        return None

def handle_chat_response(response: Dict[str, Any]):
    """Handle the chat response from the API."""
    if not response:
        return

    st.session_state.session_id = response.get("session_id")
    st.session_state.context = response.get("context")
    st.session_state.current_question = response.get("current_question")
    st.session_state.registration_complete = response.get("registration_complete", False)

    st.session_state.messages.append({
        "role": "assistant", 
        "content": response['message']
    })
    
    if response.get("suggestions") and response.get("requires_selection"):
        suggestions_text = "\n".join([
            f"{i+1}. {suggestion}" 
            for i, suggestion in enumerate(response["suggestions"])
        ])
        original_name = response.get("context", {}).get("original_name", "")
        # selection_message = (
        #     f"Here are some suggestions:\n{suggestions_text}\n\n"
        #     f"You can choose one by number or type 'keep original' to use: {original_name}"
        # )
        # st.session_state.messages.append({
        #     "role": "assistant", 
        #     "content": selection_message
        # })
    
    if response.get("event_link"):
        partner_name = response.get("context", {}).get("hackathon_details", {}).get("drillPartnerName")
        success_message = (
            "Your event has been successfully registered!"
            + (f" with partner {partner_name}" if partner_name else "")
            + f"\nYou can access it here: {response['event_link']}"
        )
        st.session_state.messages.append({
            "role": "assistant", 
            "content": success_message
        })
        
        if st.session_state.registration_complete:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Would you like to register another event? (Type 'yes' or 'no')"
            })

def reset_session():
    if st.session_state.session_id:
        try:
            requests.delete(f"{API_BASE_URL}/sessions/{st.session_state.session_id}")
        except requests.exceptions.RequestException:
            pass
    
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()

def main():

    col1, col2 = st.columns([3, 1])  

    with col1:
        st.markdown("<h1>Sarv</h1>", unsafe_allow_html=True)
        st.write("Make your Hackathon Live in 2 minutes!")
        st.write("By Where U Elevate")
        st.markdown("<hr>", unsafe_allow_html=True)

    with col2:
        image_path = "Primary logo. (1).png"  
        st.image(image_path, width=100)
    

    init_session_state()

    if not st.session_state.started:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Welcome to Sarv! Let's get started with your event registration."
        })
        response = send_message("")
        if response:
            handle_chat_response(response)
        st.session_state.started = True
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if not st.session_state.registration_complete:
        # Dynamic helper text based on current question
        helper_text = "Type your message here..."
        if st.session_state.current_question == "partnerUrl":
            helper_text = "Enter the partner organization's website URL (e.g., https://example.com)..."
        elif st.session_state.current_question == "drillName_selection":
            helper_text = "Enter a number to choose or type 'keep original'..."
        elif st.session_state.current_question == "hasPartner":
            helper_text = "Type 'yes' to add a partner organization or 'no' to continue without one..."
        
        if user_input := st.chat_input(helper_text):
            st.session_state.messages.append({
                "role": "user", 
                "content": user_input
            })
            
            response = send_message(user_input)
            if response:
                handle_chat_response(response)
            
            st.rerun()
    else:
        if user_input := st.chat_input("Type 'yes' to start new registration or 'no' to end"):
            if user_input.lower() in ['no', 'n']:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Thank you for using the Hackathon Registration Chatbot! Have a great day!"
                })
            else:
                reset_session()
                st.rerun()

    # loading spinner for partner URL processing
    if st.session_state.current_question == "partnerUrl":
        st.markdown("""
            <style>
            .partner-loading {
                margin-top: 1rem;
                padding: 1rem;
                background-color: #f8f9fa;
                border-radius: 0.5rem;
            }
            </style>
        """, unsafe_allow_html=True)

    st.markdown("""
        <style>
        .stChatMessage {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .stChatMessage[data-role="assistant"] {
            background-color: #f0f2f6;
        }
        .stChatMessage[data-role="user"] {
            background-color: #e3f2fd;
        }
        .stChatMessage a {
            color: #007bff;
            text-decoration: none;
        }
        .stChatMessage a:hover {
            text-decoration: underline;
        }
        </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
