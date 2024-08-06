import os
import stat
import shutil
import re
import zipfile
import subprocess
import streamlit as st
from streamlit_navigation_bar import st_navbar

# Set page configuration
st.set_page_config(page_title="Dockerize Your Streamlit App", initial_sidebar_state="collapsed", layout="wide")

# Define the navigation bar with logo and styles
pages = ["Home", "GitHub", "ACloudCenter.com"]
parent_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(parent_dir, "FullLogo.svg")  # Ensure your logo is in SVG format

# URLs and styles for navigation
urls = {"GitHub": "https://github.com/Josh-E-S",
        "ACloudCenter.com": "https://acloudcenter.com"}
styles = {
    "nav": {
        "background-color": "royalblue",
        "justify-content": "left",
    },
    "img": {
        "padding-right": "10px",
    },
    "span": {
        "color": "white",
        "padding": "10px 20px",
    },
    "active": {
        "background-color": "white",
        "color": "royalblue",
        "font-weight": "bold",
        "padding": "10px 20px",
    }
}
options = {
    "show_menu": False,
    "show_sidebar": False,
    "use_padding": False
}

# Display the navigation bar with the logo
try:
    page = st_navbar(
        pages,
        logo_path=logo_path,
        urls=urls,
        styles=styles,
        options=options,
    )
except Exception as e:
    st.error(f"Failed to load navigation bar: {e}")

# Application content
st.title("Dockerize Your Streamlit App")
st.write("This app helps you package your Streamlit application as a Docker container. Follow the steps below to generate a Dockerfile and build your image.")

# Initialize session state variables
if "last_github_url" not in st.session_state:
    st.session_state.last_github_url = ""
if "upload_option" not in st.session_state:
    st.session_state.upload_option = None
if "clone_success" not in st.session_state:
    st.session_state.clone_success = False
if "temp_dir_path" not in st.session_state:
    st.session_state.temp_dir_path = "temp_dir"
if "files_in_temp" not in st.session_state:
    st.session_state.files_in_temp = []

# Function to clean up or create the temporary directory
def clean_temp_dir():
    if os.path.exists(st.session_state.temp_dir_path):
        try:
            shutil.rmtree(st.session_state.temp_dir_path, onerror=on_rm_error)
        except Exception as e:
            st.error(f"Failed to delete temporary directory: {e}")
    os.makedirs(st.session_state.temp_dir_path, exist_ok=True)
    st.session_state.files_in_temp = []

# Function to handle permission errors during file removal
def on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        st.error(f"Error deleting file {path}: {e}")

# Step 1: Name Your Application
st.header("Step 1: Name Your Application")
raw_app_name = st.text_input("Enter a name for your application (e.g., MyStreamlitApp)")

# Format the app name to comply with Docker image naming conventions
def format_docker_name(name):
    # Convert to lowercase, replace spaces and invalid characters with underscores
    formatted_name = re.sub(r'[^a-z0-9]', '_', name.lower())
    # Remove leading or trailing underscores
    formatted_name = formatted_name.strip('_')
    return formatted_name

app_name = format_docker_name(raw_app_name)

# Step 2: File Upload Section
st.header("Step 2: Upload Your Project Files")

# Option to upload a ZIP archive
if st.button("(Option 1) Upload a ZIP archive"):
    st.session_state.upload_option = "zip"
zip_file = st.file_uploader("Upload your ZIP archive", type="zip", disabled=st.session_state.upload_option != "zip")

# Option to upload individual files
if st.button("(Option 2) Upload individual files"):
    st.session_state.upload_option = "individual"
uploaded_files = st.file_uploader(
    "Upload individual project files",
    type=["py", "csv", "json", "xlsx", "png", "jpg", "gif", "mp4", "toml", "yaml", "ini", "html", "css", "js", "txt", "svg"],
    accept_multiple_files=True,
    disabled=st.session_state.upload_option != "individual"
)

# Option to provide GitHub URL
if st.button("(Option 3) Use GitHub URL"):
    st.session_state.upload_option = "github"
github_url = st.text_input("Enter a GitHub URL", disabled=st.session_state.upload_option != "github")

# Handle GitHub cloning and file extraction
def handle_github_clone():
    if github_url and github_url != st.session_state.last_github_url:
        st.session_state.last_github_url = github_url
        try:
            subprocess.run(["git", "clone", github_url, st.session_state.temp_dir_path], check=True)
            st.session_state.clone_success = True
            st.session_state.files_in_temp = os.listdir(st.session_state.temp_dir_path)
            st.success("Repository cloned successfully.")
        except subprocess.CalledProcessError as e:
            st.session_state.clone_success = False
            st.error(f"Failed to clone repository: {e}")

if st.session_state.upload_option == "github":
    if st.button("Retrieve Repository"):
        clean_temp_dir()
        handle_github_clone()

# Process uploads if provided
def handle_file_uploads():
    if uploaded_files or zip_file:
        clean_temp_dir()

        if zip_file:
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                zip_ref.extractall(st.session_state.temp_dir_path)
            st.success("ZIP file extracted successfully.")

        for uploaded_file in uploaded_files:
            with open(os.path.join(st.session_state.temp_dir_path, uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        st.session_state.files_in_temp = os.listdir(st.session_state.temp_dir_path)

if st.session_state.upload_option in ["individual", "zip"]:
    handle_file_uploads()

# Add a "Clear Temporary Files" button
if st.button("Clear Temporary Files"):
    clean_temp_dir()
    st.success("Temporary files cleared.")

# Step 4: Configuration Section
st.header("Step 4: Configure Docker Settings")
base_image = st.selectbox("Select Base Image", ["python:3.9-slim", "python:3.8-slim", "python:3.7-slim"])
exposed_port = st.number_input("Expose Port", value=8501)
env_variables = st.text_area("Environment Variables (key=value format) (Optional)", "")

# Step 5: Secrets Management
st.header("Step 5: Specify Secrets")

st.write(
    """
    **Note:** If you have an existing `secrets.toml` file with sensitive information, do not include it in your uploads for security reasons.
    
    A template `secrets.toml` file will be created with example placeholder values. You should modify this file with your actual secrets after downloading the Docker package.
    """
)

secrets_example = """
# Example secrets.toml

[default]
api_key = "your-api-key-here"
db_password = "your-db-password-here"

[dev]
api_key = "dev-api-key-here"
"""

# Display a read-only text area for the example secrets.toml content
st.text_area("Example of secrets.toml file (read-only):", value=secrets_example, height=200, disabled=True)

# Step 6: Generate and Preview Dockerfile
st.header("Step 6: Generate and Preview Dockerfile")

# Ask the user to select the main file if there are multiple .py files uploaded or in the repo
main_file = "app.py"
if st.session_state.files_in_temp:
    py_files = [f for f in st.session_state.files_in_temp if f.endswith('.py')]
    if py_files:
        main_file = st.selectbox("Select the main Python file to run your Streamlit app", py_files)

if st.session_state.files_in_temp and app_name:
    dockerfile_content = (
        f"# Use the selected base image\n"
        f"FROM {base_image}\n\n"
        f"# Set the working directory in the container\n"
        "WORKDIR /app\n\n"
        "# Copy the requirements file into the container\n"
        "COPY requirements.txt .\n\n"
        "# Install any needed packages specified in requirements.txt\n"
        "RUN pip install --no-cache-dir -r requirements.txt\n\n"
        "# Install Git\n"
        "RUN apt-get update && apt-get install -y git && apt-get clean\n\n"
        "# Copy the rest of the project files into the container\n"
        "COPY . .\n\n"
        "# Expose the specified port for Streamlit\n"
        f"EXPOSE {exposed_port}\n\n"
        "# Set environment variables\n"
        + "".join([f"ENV {line}\n" for line in env_variables.splitlines() if line.strip()])
        + "\n"
        "# Run the Streamlit app\n"
        f"CMD [\"streamlit\", \"run\", \"{main_file}\", \"--server.port={exposed_port}\", \"--server.address=0.0.0.0\"]"
    )

    st.code(dockerfile_content, language="dockerfile")

    # Save Dockerfile and secrets.toml to temporary directory
    dockerfile_path = os.path.join(st.session_state.temp_dir_path, "Dockerfile")
    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_content)
    with open(os.path.join(st.session_state.temp_dir_path, "secrets.toml"), "w") as f:
        f.write(secrets_example)

    # Check if Dockerfile was created successfully
    if os.path.exists(dockerfile_path):
        with open(dockerfile_path, "r") as f:
            st.code(f.read(), language="dockerfile")
        st.success("Dockerfile created successfully.")
    else:
        st.error("Failed to create Dockerfile.")

    # Create a ZIP file containing the Dockerfile, secrets.toml, and project files
    zip_filename = f"{app_name}_docker_files.zip"
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        # Explicitly add Dockerfile
        zipf.write(dockerfile_path, arcname="Dockerfile")
        # Explicitly add secrets.toml
        zipf.write(os.path.join(st.session_state.temp_dir_path, "secrets.toml"), arcname="secrets.toml")
        # Add all other files
        for file in st.session_state.files_in_temp:
            if file not in ["Dockerfile", "secrets.toml"]:  # Avoid duplicates
                zipf.write(os.path.join(st.session_state.temp_dir_path, file), arcname=file)

    # Display contents of the ZIP file
    st.write("Contents of the ZIP file:")
    with zipfile.ZipFile(zip_filename, 'r') as zipf:
        for filename in zipf.namelist():
            st.write(filename)

    # Step 7: Build and Run Instructions
    st.header("Step 7: Build and Run Instructions")
    st.write(
        f"""
        Follow these steps to build and run your Docker container:

        1. **Download the Dockerfile and Project Files**: Click the button below to download a ZIP file containing the Dockerfile, a template secrets.toml, and your project files.
        """
    )

    # Download button for the ZIP file
    if os.path.exists(zip_filename):
        st.download_button("Download Dockerfile and Project Files", data=open(zip_filename, "rb"), file_name=zip_filename)
    else:
        st.error("Failed to create ZIP file.")

    st.write(
        f"""
        2. **Extract the ZIP File**: Unzip the downloaded file to a new directory.

        3. **Edit the `secrets.toml` File**: Open the `secrets.toml` file and replace placeholder values with your actual secrets.

        4. **Navigate to the Directory**: Open your terminal and navigate to the directory where you extracted the files. Typically, files download to the `Downloads` folder:
           ```
           cd ~/Downloads/{app_name}_docker_files
           ```

        5. **Build the Docker Image**: Run the following command to build your Docker image. Make sure you are in the same directory as your Dockerfile:
           ```
           docker build -t {app_name} .
           ```

        6. **Run the Docker Container**: Use the command below to run your container with a specific name. This will map your application to the specified port:
           ```
           docker run --name {app_name}_container -p {exposed_port}:{exposed_port} {app_name}
           ```

        Once the container is running, you can access your Streamlit app in your browser at `http://localhost:{exposed_port}`.
        """
    )

    # Cleanup temporary files after download
    if st.button("Clear Temporary Files After Download"):
        clean_temp_dir()
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
        st.success("Temporary files and ZIP file cleared.")
else:
    st.warning("Please complete all steps to proceed. Ensure you've named your app and uploaded necessary files or provided a GitHub URL.")