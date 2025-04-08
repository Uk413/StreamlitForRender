import streamlit as st
import requests
from typing import Dict, Any
import json
import uuid

# API_BASE_URL = "http://localhost:8000"
API_BASE_URL = "https://utkarsh134-fastapi-hackathonin2mins.hf.space"

EVENT_TYPES = [
    "WORKSHOP",
    "WEBINAR",
    "MASTERCLASS",
    "INNOVATIONHACKATHON",
    "SQUADPROGRAM",
    "CASESTUDY",
    "HIRINGHACKATHON",
    "INNOVATION",
    "TECHCONFERENCES",
    "BOOTCAMP",
    "STARTUP",
    "CONCLAVE",
    "CONTRACTUAL",
    "IDEATHON",
    "INTERNALHACKATHON",
    "SMARTINDIAHACKATHON"
]

def init_session_state():
    if 'current_question' not in st.session_state:
        st.session_state.current_question = "drillSubCategory"
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'registration_complete' not in st.session_state:
        st.session_state.registration_complete = False
    if 'started' not in st.session_state:
        st.session_state.started = False
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'show_event_types' not in st.session_state:
        st.session_state.show_event_types = True

def send_message(message: str) -> Dict[str, Any]:
    try:
        payload = {
            "session_id": st.session_state.session_id,
            "message": message,
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
    st.session_state.current_question = response.get("current_question")
    st.session_state.registration_complete = response.get("registration_complete", False)
    
    # Hide event type buttons after they've been used
    if st.session_state.current_question != "drillName":
        st.session_state.show_event_types = False

    # Display the assistant's message
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response['message']
    })
    
    # Special handling for event completion and links
    if response.get("event_link"):
        success_message = (
            "Your event has been successfully registered!"
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

def handle_event_type_selection(event_type):
    # Add user's event type selection as a message
    st.session_state.messages.append({
        "role": "user", 
        "content": event_type
    })
    
    # Send the event type to the backend
    response = send_message(event_type)
    if response:
        handle_chat_response(response)
    
    # Hide event type buttons after selection
    st.session_state.show_event_types = False

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

    # Initialize chat with welcome message and event type question
    if not st.session_state.started:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Welcome to Sarv! Let's get started with your event registration."
        })
        st.session_state.messages.append({
            "role": "assistant",
            "content": "What type of event do you want to host?"
        })
        st.session_state.started = True
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Display event type selection buttons if showing event types
    if st.session_state.show_event_types:
        st.write("Please select an event type:")
        
        # Create a 4x4 grid of buttons for event types
        cols = st.columns(4)
        for i, event_type in enumerate(EVENT_TYPES):
            col_index = i % 4
            with cols[col_index]:
                # Create a more user-friendly display name with spaces
                display_name = " ".join([word.capitalize() for word in event_type.split()])
                if st.button(display_name, key=f"btn_{event_type}"):
                    handle_event_type_selection(event_type)
                    st.rerun()
    
    # Handle subsequent interactions if not complete
    if not st.session_state.registration_complete:
        # Update helper text based on current question
        helper_text = "Type your message here..."
        if st.session_state.current_question == "drillName":
            helper_text = "Enter a name for your event, or ask for help..."
        elif st.session_state.current_question == "partnerUrl":
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
                    "role": "user",
                    "content": user_input
                })
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Thank you for using Sarv! Have a great day!"
                })
            else:
                st.session_state.messages.append({
                    "role": "user",
                    "content": user_input
                })
                reset_session()
                st.rerun()

    # Loading spinner for partner URL processing
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

    # CSS styling for chat interface
    st.markdown("""
    <style>
    /* Base styles */
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        color: #000000;
    }

    .stChatMessage[data-role="assistant"] {
        background-color: #f0f2f6;
    }

    .stChatMessage[data-role="user"] {
        background-color: #e3f2fd;
    }

    .stChatMessage[data-naming-conversation="true"] {
        border-left: 4px solid #4CAF50;
    }

    .stChatMessage a {
        color: #007bff;
        text-decoration: none;
    }

    .stChatMessage a:hover {
        text-decoration: underline;
    }

    .stButton button {
        width: 100%;
        margin-bottom: 8px;
        border-radius: 4px;
        background-color: #f0f2f6;
        border: 1px solid #dbe1e9;
        padding: 6px 10px;
        font-size: 0.9em;
        color: #000000;
        text-transform: uppercase;
        font-weight: 600;
    }

    .stButton button:hover {
        background-color: #dbe1e9;
    }

    /* Dark mode styles */
    @media (prefers-color-scheme: dark) {
        .stChatMessage {
            color: #f1f1f1;
        }

        .stChatMessage[data-role="assistant"] {
            background-color: #1f2937;
        }

        .stChatMessage[data-role="user"] {
            background-color: #374151;
        }

        .stChatMessage[data-naming-conversation="true"] {
            border-left: 4px solid #10b981;
        }

        .stChatMessage a {
            color: #60a5fa;
        }

        .stButton button {
            background-color: #374151;
            border: 1px solid #4b5563;
            color: #f1f1f1;
            text-transform: uppercase;
            font-weight: 600;
        }

        .stButton button:hover {
            background-color: #4b5563;
        }
    }
    </style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
