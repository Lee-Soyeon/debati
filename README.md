# Debati 🐶

Debati is a debate AI for upper elementary school students! Users can interact with Debati through a web interface. Debati generates and returns answers to users' questions, understanding and responding to questions in real-time interaction.

## Table of Contents
- [Installation Guide](#installation-guide)
- [How to Run](#how-to-run)
- [Usage](#usage)
- [Inquiries](#inquiries)
- [License](#license)
- [Contribution](#contribution)

## Installation Guide 🚀

### System Requirements
- Python 3.8 or higher
- Package management tool Poetry
- OpenAI API Key

### Installing Package Management Tool Poetry
Install 'Poetry', a tool for managing packages in Python. Poetry helps automate package version management.

### Package Installation
Install the libraries required to run Debati. Libraries are installed using Poetry, a Python package installation tool. To proceed with the installation, navigate to the project location in the terminal and enter the following command:

```
poetry install
```

## Streamlit Configuration
For the Streamlit web interface, add the necessary settings to the `.streamlit/secrets.toml` file. This file is used to store configuration information for the Streamlit app. Here's an example configuration:

```toml
[api]
openai_api_key = "your_openai_api_key_here"
[settings]
temperature = 1
system_prompt = "You are a helpful assistant."
```

## How to Run 🖥️

### Running Locally
You can run the code using Poetry with the following command:

#### Running Debati (Web Interface)
```
poetry run streamlit run streamlit_app.py
```

### Streamlit Web Interface Configuration
No additional setup is required to interact with Debati through the web interface. You can run the Streamlit application locally using the command provided in the How to Run section above.

Additionally, Debati is accessible on the web through [this link](https://singwan.school/). You can start interacting with Debati immediately by clicking on this link.

## Usage 📘

### Using the Web Interface
To interact with Debati on the web interface, run the Streamlit application and access the URL in a web browser. Users can start a conversation with Debati by entering messages in the chat input field. Debati responds to users' questions and interacts in real-time.

## Inquiries 💬

If you have any questions or issues about the project, please let us know through the issue tracker.

## Contribution 🤝

This project follows Open Source principles in every aspect! Therefore, contributions to this project are welcome!
- Implement new features.
- Fix bugs.
- Update documentation.

If you have any questions, opinions, or suggestions about the project, please feel free to share them! Let's improve together.
