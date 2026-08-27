import streamlit as st
import requests
import uuid
import time
import pandas as pd
import os


# ==============================
# Rasa API Configuration
# ==============================

RASA_URL = "https://old-galvanize-thesis.ngrok-free.dev/webhooks/rest/webhook"


# ==============================
# Page Configuration
# ==============================

st.set_page_config(
    page_title="Gym and Fitness Chatbot",
    page_icon="🤖💪",
    layout="centered"
)


# ==============================
# Session Management
# ==============================

if "sender_id" not in st.session_state:

    st.session_state.sender_id = str(uuid.uuid4())


if "messages" not in st.session_state:

    st.session_state.messages = []



# ==============================
# Header Section
# ==============================

header_col1, header_col2 = st.columns([8, 1])


with header_col1:

    st.title("🤖 Gym and Fitness Chatbot")

    st.caption(
        "Your AI fitness assistant that recommends exercises based on "
        "body part, equipment, and difficulty level."
    )


with header_col2:

    st.write("")

    if st.button("🗑", help="Clear conversation"):

        st.session_state.messages = []

        st.session_state.sender_id = str(uuid.uuid4())

        st.rerun()



st.divider()



# ==============================
# Chat History
# ==============================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.write(message["content"])



# ==============================
# User Input
# ==============================

user_input = st.chat_input(
    "Example: Recommend beginner chest exercises using dumbbells"
)



if user_input:


    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )


    with st.chat_message("user"):

        st.write(user_input)



    # ==============================
    # Connect with Rasa
    # ==============================

    try:


        start_time = time.time()


        response = requests.post(

            RASA_URL,

            json={

                "sender":
                st.session_state.sender_id,

                "message":
                user_input

            },

            timeout=10

        )


        response_time = round(
            time.time() - start_time,
            2
        )


        response.raise_for_status()


        rasa_response = response.json()



        # ==============================
        # Bot Response
        # ==============================


        if rasa_response:


            for message in rasa_response:


                if "text" in message:


                    bot_text = message["text"]


                    st.session_state.messages.append(

                        {

                            "role": "assistant",

                            "content": bot_text

                        }

                    )


                    with st.chat_message("assistant"):

                        st.write(bot_text)



            st.caption(
                f"⚡ Response time: {response_time}s"
            )


        else:


            bot_text = (
                "Sorry, I could not understand your request. "
                "Please try again."
            )


            st.session_state.messages.append(

                {

                    "role": "assistant",

                    "content": bot_text

                }

            )


            with st.chat_message("assistant"):

                st.warning(bot_text)



    except requests.exceptions.ConnectionError:


        st.error(
            """
            ❌ Cannot connect to Rasa server.

            Please make sure:

            1. Rasa action server is running
            2. Rasa API server is running
            """
        )


    except requests.exceptions.Timeout:


        st.error(
            "⏳ Rasa response timeout. Please try again."
        )


    except Exception as e:


        st.error(
            f"Unexpected error: {e}"
        )



# ==============================
# Feedback Section
# ==============================

st.divider()


st.subheader("⭐ Rate Your Experience")


rating = st.slider(

    "How useful was the chatbot recommendation?",

    min_value=1,

    max_value=5,

    value=5

)



if st.button("Submit Feedback"):


    feedback_file = "feedback.csv"


    feedback_data = {

        "sender_id":
        st.session_state.sender_id,

        "rating":
        rating

    }



    if os.path.exists(feedback_file):


        df = pd.read_csv(feedback_file)


        df = pd.concat(

            [

                df,

                pd.DataFrame(
                    [feedback_data]
                )

            ],

            ignore_index=True

        )


    else:


        df = pd.DataFrame(
            [feedback_data]
        )



    df.to_csv(

        feedback_file,

        index=False

    )


    st.success(
        "Thank you for your feedback!"
    )
