from __future__ import annotations

import re
import logging
from collections.abc import Generator
from typing import Any

import streamlit as st
from langchain.schema import AIMessage, BaseMessage, HumanMessage, SystemMessage

from config.app_config import AppConfig, init_chat_model
from config.streamlit_config import StreamlitAppConfig
from utils.logging_utils import create_log_message
from utils.message_utils import prepare_chat_messages, UserStance

ASSISTANT_AVATAR_URL = "https://avatars.slack-edge.com/2023-11-19/6217189323093_136df1241dc3492d67d6_192.png"
AVATARS = {
"assistant": ASSISTANT_AVATAR_URL
}

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def handle_chat_interaction(app_config: StreamlitAppConfig) -> None:
    """
    Manages the chat interaction, including displaying the chat interface and handling user inputs and responses.

    This function creates a user interface for the chatbot in a web browser using Streamlit.
    It maintains the session state to keep track of the conversation history and uses the
    chat model to generate responses to user inputs.

    Args:
        app_config (StreamlitAppConfig): The configuration object for the app.
    """
    # Retrieve the current debate topic from the configuration
    debate_topic = app_config.debate_topic

    if "user_stance" in st.session_state:
        user_stance = st.session_state.user_stance
    else:
        user_stance = UserStance.UNDECIDED

    # Initialize session state for conversation history
    if "thread_messages" not in st.session_state:
        st.session_state.thread_messages = [
            {"role": "assistant", "content": f"{debate_topic}에 대해 궁금한 점을 자유롭게 물어보세요."}
        ]

    if "companion_id" in st.session_state:
        companion_name = st.session_state.companion_id
    else:
        companion_name = f"토론 주제: {debate_topic}"

    # Initialize or update the progress bar
    if "debate_score" not in st.session_state:
        st.session_state.debate_score = 0

    st.title(companion_name)

    # Display existing chat messages
    display_messages(st.session_state.thread_messages)

    # Accept user input and generate responses
    user_input = st.chat_input(f"Message {companion_name}...")
    logging.info(
        create_log_message(
            "Received a question from user",
            user_input=user_input,
        )
    )

    if user_input:
        user_message = {"role": "user", "content": user_input}
        st.session_state.thread_messages.append(user_message)
        display_messages([user_message])

        try:
            # If Firebase is enabled, override the config with the one from Firebase
            if app_config.firebase_enabled:
                companion_id = st.session_state.companion_id
                app_config.load_config_from_firebase(companion_id)
                logging.info("Override configuration with Firebase settings")

            # Evaluate debate performance after each message
            st.session_state.debate_score = evaluate_debate_performance(app_config, st.session_state.thread_messages)

            # Format messages for chat model processing with appropriate system prompt
            formatted_messages = format_messages(st.session_state.thread_messages)
            logging.info(
                create_log_message(
                    "Sending messages to OpenAI API",
                    messages=formatted_messages,
                )
            )

            with st.chat_message("assistant", avatar=ASSISTANT_AVATAR_URL):
                message_placeholder = st.empty()
                response_message = ""

            # Generate response using chat model
            for message_chunk in ask_question(formatted_messages, app_config, user_stance):
                logging.info(
                    create_log_message(
                        "Received response from OpenAI API",
                        message_chunk=message_chunk,
                    )
                )
                response_message += message_chunk
                message_placeholder.markdown(response_message + "▌")
            message_placeholder.markdown(response_message)

            assistant_message = {"role": "assistant", "content": response_message}
            st.session_state.thread_messages.append(assistant_message)
        except Exception:  # pylint: disable=broad-except
            logging.error("Error in chat interface: ", exc_info=True)
            error_message = (
                "Sorry, I encountered a problem while processing your request."
            )
            st.error(error_message)

    # Check if the user has already chosen a stance
    if "user_stance" not in st.session_state and len(st.session_state.thread_messages) > 1:
        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR_URL):
            # Display stance selection interface
            user_stance = display_stance_selection(debate_topic)

        if user_stance != UserStance.UNDECIDED:
            st.session_state.user_stance = user_stance

            if user_stance == UserStance.PRO:
                initial_message = f"당신이 {debate_topic}에 찬성함에 따라, 저는 반대 입장에서 토론을 진행합니다."
            else:
                initial_message = f"당신이 {debate_topic}에 반대함에 따라, 저는 찬성 입장에서 토론을 진행합니다."

            # If user stance is selected, reset thread_messages for debating phase
            # Reset thread messages for debating phase
            st.session_state.thread_messages = [{"role": "assistant", "content": initial_message}]
            # Display reset messages
            display_messages(st.session_state.thread_messages)


    if "user_stance" in st.session_state and len(st.session_state.thread_messages) > 2:
        # Update progress bar and feedback
        progress_bar = st.progress(st.session_state.debate_score / 10)

def display_messages(messages: list[dict[str, Any]]) -> None:
    """
    Displays chat messages in the Streamlit interface.

    This function iterates over a list of messages and displays them in the Streamlit chat interface.
    Each message is displayed with the appropriate role (user or assistant).

    Args:
        messages (list[dict[str, Any]]): A list of message dictionaries, where each message has a 'role' and 'content'.
    """
    for message in messages:
        role = message["role"]
        with st.chat_message(role, avatar=AVATARS.get(role)):
            st.markdown(message["content"])

def display_stance_selection(debate_topic: str) -> UserStance:
    """
    Displays the interface for the user to select their stance on the topic.
    """
    st.write(f"{debate_topic}에 대한 당신의 입장은 무엇인가요?")
    cols = st.columns(2)
    if cols[0].button("찬성", use_container_width=True):
        return UserStance.PRO
    if cols[1].button("반대", use_container_width=True):
        return UserStance.CON
    return UserStance.UNDECIDED

def format_messages(thread_messages: list[dict[str, Any]]) -> list[BaseMessage]:
    """Formats messages for the chatbot's processing."""
    formatted_messages: list[BaseMessage] = []

    for msg in thread_messages:
        if msg["role"] == "user":
            formatted_messages.append(HumanMessage(content=msg["content"]))
        else:
            formatted_messages.append(AIMessage(content=msg["content"]))

    return formatted_messages


def ask_question(
        formatted_messages: list[BaseMessage], app_config: AppConfig, user_stance: UserStance
) -> Generator[str, None, None]:
    """
    Initialize a chat model and stream the chat conversation. This includes optional prefix messages loaded
    from a file or settings, followed by the main conversation messages. The function adjusts its responses based
    on the user's stance in the debate and yields each chunk of the response content as it is received from the Chat API.

    Args:
        formatted_messages (list[BaseMessage]): List of formatted messages constituting the main conversation.
        app_config (AppConfig): Configuration parameters for the application.
        user_stance (UserStance): The user's stance in the debate, influencing the direction of the conversation.

    Yields:
        Generator[str, None, None]: Generator yielding each content chunk from the Chat API responses.
    """
    chat = init_chat_model(app_config)
    prepared_messages = prepare_chat_messages(formatted_messages, app_config, user_stance)
    for chunk in chat.stream(prepared_messages):
        yield str(chunk.content)

def evaluate_debate_performance(app_config: StreamlitAppConfig, thread_messages: list[dict[str, Any]]) -> float:
    """
    Evaluates the student's performance in the debate using AI and returns the score and feedback.

    Args:
        app_config (StreamlitAppConfig): The application configuration.
        thread_messages (list[dict[str, Any]]): The list of messages in the debate thread.

    Returns:
        tuple[float, str]: A tuple containing the debate score and feedback.
    """
    messages_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in thread_messages])
    evaluation_prompt = app_config.debate_evaluation_prompt

    chat = init_chat_model(app_config)
    formatted_messages = [SystemMessage(content=evaluation_prompt), HumanMessage(content=messages_str)]
    resp = chat.generate([formatted_messages])
    response = resp.generations[0][0].text

    # Extract score and feedback from AI response
    score_match = re.search(r"\b\d+(\.\d+)?\b", response)
    debate_score = float(score_match.group()) if score_match else 0.0

    if debate_score > 10:
        debate_score = 10.0

    logging.info(create_log_message("Evaluation Response", response=response, debate_score=debate_score))

    return debate_score


def display_companion_id_input() -> str | None:
    """
    Displays an input field in the Streamlit sidebar for the user to enter or change the companion_id.

    Returns:
        Optional[str]: The entered Companion ID, or None if not entered.
    """
    st.sidebar.title("Companion ID Settings")
    companion_id = st.sidebar.text_input("Enter Companion ID", key="companion_id_input")
    return companion_id


def main():
    """Main function to run the Streamlit chatbot app."""
    logging.info("Starting Streamlit chatbot app")

    app_config = StreamlitAppConfig()
    app_config.load_config()

    if app_config.firebase_enabled:
        companion_id = display_companion_id_input()
        if not companion_id:
            st.markdown("👈 상단 왼쪽 모서리에 있는 사이드바를 열어 Companion ID를 입력해 주세요.")
            return
        if (
            "companion_id" not in st.session_state
            or st.session_state.companion_id != companion_id
        ):
            st.session_state.companion_id = companion_id
            st.session_state.thread_messages = []
        app_config.load_config_from_firebase(companion_id)
        logging.info("Override configuration with Firebase settings")

    # Display chat interface
    handle_chat_interaction(app_config)


if __name__ == "__main__":
    main()
