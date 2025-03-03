import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Streamlit Chat", page_icon="💬")
st.title("Chat Bot")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

if not st.session_state.setup_complete:
    st.subheader('Personal Information', divider='rainbow')

    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

    name = st.text_input(label="Name", max_chars=40, value=st.session_state["name"], placeholder="Enter your name..." )
    
    experience = st.text_area(label="Experience", value=st.session_state["experience"], height=None, max_chars=200,placeholder="Describe your experience..." )

    skills = st.text_area(label="Skills (Seperate with comma (,))", value=st.session_state["skills"], height=None, max_chars=200,placeholder="List your skills..." )

    st.subheader('Company and Position', divider='rainbow')

    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
            "Choose Level",
            key='visibility',
            options=["Junior","Mid-level","Senior"]
        )

    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"

    with col2:
        st.session_state["position"] = st.selectbox(
            "Choose a Position",
            ("Data Scientist","Data Engineer","ML Engineer", "BI Analyst", "Financial Analyst")
        )

    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"

    st.session_state["company"] = st.selectbox(
        "Choose a Company",
        ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify")
    )

    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting Interview...")

if (st.session_state.setup_complete 
    and not st.session_state.feedback_shown 
    and not st.session_state.chat_complete):
    
    st.info(
        """
        Start by introducing yourself
        """,
        icon="👋"
    )

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o-mini"

    if not st.session_state.messages:
        st.session_state.messages = [
            {"role":"system", "content":f"""You are an HR Executive that interviews
            an interviewee called {st.session_state["name"]} with experience {st.session_state["experience"]} and skills {st.session_state["skills"]}.
            You should interview them for the position {st.session_state["level"]} {st.session_state["position"]} 
            at the company {st.session_state["company"]}."""}
        ]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your answer.", max_chars=1000):
            st.session_state.messages.append({"role":"user", "content":prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[
                            {"role":m["role"], "content":m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream=True
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append({"role":"assistant", "content": response})
            
            st.session_state.user_message_count += 1
    
    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")

if st.session_state.feedback_shown:
    st.subheader("Feedback")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    feedback_completion = feedback_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": """
            You are a helpful tool that provides feedback on an interviewee performance.
            Before the Feedback give a score of 1 to 10.
            Follow this format:
            Overall Score: //Your score
            Feedback: //Here put your feedback
            Give only the feedback do not ask for additional questions.
            """},
            {"role":"user","content":f"""This is the interview you need to evaluate.
                                         Keep in mind that you are only a tool and you should
                                         not engage in a conversation:
                                         {conversation_history}"""}
        ]
    )

    st.write(feedback_completion.choices[0].message.content)

    if st.button("Restart Interview", type="primary"):

        streamlit_js_eval(js_expressions="parent.window.location.reload()")