import streamlit as st
import time
import json
import requests
import re
import shutil
import os
import asyncio
import concurrent.futures

from dataclasses import dataclass
from enum import Enum, auto
from transformers import AutoTokenizer
from services.nv_retriever_client import NVRetriever
from services.oss_retriever_client import OSSRetriever

class EndpointType(Enum):
    AZUREML = auto()
    PROMPTFLOW = auto()
    VM = auto()
    API_CATALOG = auto()

@dataclass
class EndpointConfig:
    url: str
    key: str
    model: str
    deployment_name: str
    health_url_extn: str

def load_endpoints_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    nim_off_endpoints = {}
    nim_on_endpoints = {}
    
    for endpoint_type, config in data['nim_off_endpoints'].items():
        nim_off_endpoints[EndpointType[endpoint_type]] = EndpointConfig(**config)
    
    for endpoint_type, config in data['nim_on_endpoints'].items():
        nim_on_endpoints[EndpointType[endpoint_type]] = EndpointConfig(**config)
    
    return nim_off_endpoints, nim_on_endpoints

config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
nim_off_endpoints, nim_on_endpoints = load_endpoints_from_json(config_path)

nim_off_ttft = 0
nim_off_time_to_next_token = []
nim_off_tokens_received = 0

nim_on_ttft = 0
nim_on_time_to_next_token = []
nim_on_tokens_received = 0

nv_retriever_client = NVRetriever(base_url="http://localhost:1984")
oss_retriever_client = OSSRetriever()

tokenizer = AutoTokenizer.from_pretrained("mistralai/Mixtral-8x7B-Instruct-v0.1", token="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")

def generate_headers(endpoint_type, endpoint_config):
    headers = {
        'Content-Type': 'application/json'
    }

    if endpoint_config.key != "":
        headers.update({'Authorization': f'Bearer {endpoint_config.key}'})

    if endpoint_config.deployment_name != "":
        headers.update({'azureml-model-deployment': endpoint_config.deployment_name})
    
    return headers

def generate_body(endpoint_type, endpoint_config, messages):
    body = {
        "model": endpoint_config.model,
        "messages": messages,
        "max_tokens": 1024,
        "stream": True
    }
    return body

def check_health(endpoint_type, endpoint_config):
    headers = generate_headers(endpoint_type, endpoint_config)
    health_url = endpoint_config.url + endpoint_config.health_url_extn
    try:
        response = requests.get(health_url, headers=headers)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        return False

def get_prompt_with_context(prompt, retriever_client):
    context = retriever_client.retrieve(prompt)
    prompt = f"You are an AI assistant in a Financial company. Answer the question based \
    on the provided context, prioritize higher scores. Site the relevant part of the context under \"Sources\" section. \
    \n\n Question: {prompt} \
    \n\n Context: \n {context}."
    return prompt

def get_os_stream_response(endpoint_type, endpoint_config, messages):
    url, key, deployment_name, model = endpoint_config.url, endpoint_config.key, endpoint_config.deployment_name, endpoint_config.model
    headers = generate_headers(endpoint_type, endpoint_config)
    body = generate_body(endpoint_type, endpoint_config, messages)

    error_msg = ""
    error_response_code = -1

    global nim_off_ttft
    global nim_off_tokens_received
    global nim_off_time_to_next_token

    start_time = time.monotonic()
    most_recent_received_token_time = time.monotonic()
    
    try:
        with requests.post(
            url + "/v1/chat/completions",
            json=body,
            stream=True,
            timeout=180,
            headers=headers,
        ) as response:
            if response.status_code != 200:
                error_msg = response.text
                error_response_code = response.status_code
                response.raise_for_status()
            for chunk in response.iter_lines(chunk_size=None):
                # Parse chunk
                chunk = chunk.strip()
                if not chunk:
                    continue
                stem = "data: "
                chunk = chunk[len(stem) :]
                if chunk == b"[DONE]":
                    continue
                data = json.loads(chunk)
                
                # Check errors
                if "error" in data:
                    error_msg = data["error"]["message"]
                    error_response_code = data["error"]["code"]
                    raise RuntimeError(data["error"]["message"])                
                
                delta = data["choices"][0]["delta"]
                if delta.get("content", None):
                    nim_off_tokens_received += 1
                    if not nim_off_ttft:
                        nim_off_ttft = time.monotonic() - start_time
                        nim_off_time_to_next_token.append(nim_off_ttft)
                    else:
                        nim_off_time_to_next_token.append(
                            time.monotonic() - most_recent_received_token_time
                        )
                    most_recent_received_token_time = time.monotonic()                    
                    yield delta["content"]

    except Exception as e:
        print(f"Warning Or Error: {error_msg} {error_response_code}")

def get_nim_stream_response(endpoint_type, endpoint_config, messages):
    url, key, deployment_name, model = endpoint_config.url, endpoint_config.key, endpoint_config.deployment_name, endpoint_config.model
    headers = generate_headers(endpoint_type, endpoint_config)
    body = generate_body(endpoint_type, endpoint_config, messages)

    error_msg = ""
    error_response_code = -1

    global nim_on_ttft
    global nim_on_tokens_received
    global nim_on_time_to_next_token

    start_time = time.monotonic()
    most_recent_received_token_time = time.monotonic()

    try:
        with requests.post(
            url + "/v1/chat/completions",
            json=body,
            stream=True,
            timeout=180,
            headers=headers,
        ) as response:
            if response.status_code != 200:
                error_msg = response.text
                error_response_code = response.status_code
                response.raise_for_status()
            for chunk in response.iter_lines(chunk_size=None):
                # Parse chunk
                chunk = chunk.strip()
                if not chunk:
                    continue
                stem = "data: "
                chunk = chunk[len(stem) :]
                if chunk == b"[DONE]":
                    continue
                data = json.loads(chunk)                
                
                # Check errors
                if "error" in data:
                    error_msg = data["error"]["message"]
                    error_response_code = data["error"]["code"]
                    raise RuntimeError(data["error"]["message"])                
                
                delta = data["choices"][0]["delta"]
                if delta.get("content", None):
                    nim_on_tokens_received += 1
                    if not nim_on_ttft:
                        nim_on_ttft = time.monotonic() - start_time
                        nim_on_time_to_next_token.append(nim_on_ttft)
                    else:
                        nim_on_time_to_next_token.append(
                            time.monotonic() - most_recent_received_token_time
                        )
                    most_recent_received_token_time = time.monotonic()                    
                    yield delta["content"]

    except Exception as e:
        st.error(f"Warning Or Error: {error_msg} {error_response_code}")

def manage_uploaded_files(uploaded_files):
    try:
        upload_dir = "uploaded_files"
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
        os.makedirs(upload_dir)
        
        filepaths = []
        for uploaded_file in uploaded_files:
            # Save each file to the "uploaded_files" directory
            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            filepaths.append(file_path)
        
        return filepaths
    except Exception as e:
        st.error(f"Failed to manage uploaded files. Reason: {e}")
        return None

def create_db(filepaths, container):
    with container:
        nim_off_bar = st.progress(0, text="Creating DB using OSS")
        start_time = time.monotonic()
        st.session_state.nv_stack_off_db_ready = oss_retriever_client.process_pdfs(filepaths, False, nim_off_bar.progress)
        nim_off_time = time.monotonic() - start_time
        nim_off_bar.empty() 
        nim_off_final = st.progress(100, text="OSS DB created")
        nim_on_bar = st.progress(0, text="Creating DB using NeMo Retriever")
        start_time = time.monotonic()
        st.session_state.nv_stack_on_db_ready = nv_retriever_client.add_to_collection(filepaths, nim_on_bar.progress)
        nim_on_time = time.monotonic() - start_time
        nim_on_bar.empty() 
        nim_on_final = st.progress(100, text="NeMo Retriever DB created")
        perf_gain = nim_off_time/nim_on_time
        metrics = "OSS time: " +  "{:.0f}".format(nim_off_time) +  " seconds"  + "\tNeMo Retriever time: " + "{:.2f}".format(nim_on_time) + " seconds"
        st.markdown(f'''`{metrics}`''')        
        gain = "Perf gain: "+"{:.1f}".format(perf_gain) + "X🚀"
        st.markdown(f'''**{gain}**''')

if "nv_stack_off_db_ready" not in st.session_state:
    st.session_state.nv_stack_off_db_ready = False
if "nv_stack_on_db_ready" not in st.session_state:
    st.session_state.nv_stack_on_db_ready = False

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Init uploaded files
if "uploaded_filepaths" not in st.session_state:
    st.session_state.uploaded_filepaths = []

# Set the title of the Streamlit app"
st.set_page_config(layout="wide", page_title="NeMo Retriever demo")
st.markdown("""
    <style>
    .new-session-button {
        padding-top: 10px;
        padding-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)    

st.markdown("""
    <style>
    .db-button {
        padding-top: 27px;
        padding-bottom: 22px;
    }
    </style>
    """, unsafe_allow_html=True)

cols = st.columns([4, 2, 2, 1])
with cols[0]:
    st.title('NeMo Retriever OFF vs ON')
    st.write('Config: NV-Embed-v1 (1 A100) + NV-Rerank-QA-Mistral-4Bs (1 A100) + Retriever MS (1 A100)')
with cols[2]:
    endpoint_type = st.selectbox("Endpoint Type", [endpoint.name for endpoint in EndpointType])
    st.session_state.endpoint_choice = EndpointType[endpoint_type]

cols[3].markdown('<div class="new-session-button"></div>', unsafe_allow_html=True)
with cols[3]:
    if cols[3].button('New session'):
        st.session_state.messages = []

col1, col2, col3 = st.columns([3, 1, 4])

with col1:
    uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        filepaths = manage_uploaded_files(uploaded_files)
        if filepaths:
            st.session_state.uploaded_filepaths = filepaths[:]
            st.toast(f"Uploaded {len(filepaths)} files")

col2.markdown('<div class="db-button"></div>', unsafe_allow_html=True)
with col2:
    if st.button('Create DB'):
        if len(st.session_state.uploaded_filepaths) != 0:
            create_db(st.session_state.uploaded_filepaths, col3)
        st.session_state.uploaded_filepaths.clear()

col1, _, col2, _ = st.columns([5,1,5,1])

endpoint_type = st.session_state.endpoint_choice
nim_off_config = nim_off_endpoints[endpoint_type]
nim_on_config = nim_on_endpoints[endpoint_type]

with col1:
    url = st.text_input("NIM-OFF endpoint config", value=nim_off_config.url, key="nim-off-url")
    nim_off_config.url = url
    model = st.text_input("Model", value=nim_off_config.model, key="nim-off-model", label_visibility="collapsed")
    nim_off_config.model = model

with col2:
    url = st.text_input("NIM-ON endpoint config", value=nim_on_config.url, key="nim-on-url")
    nim_on_config.url = url
    model = st.text_input("Model", value=nim_on_config.model, key="nim-on-model", label_visibility="collapsed")
    nim_on_config.model = model

with col1:
    col3, _, col4, col5 = st.columns([3, 2, 1, 2])
    with col3:
        st.write("NeMo Retriever-OFF with NIM-OFF")
    with col4:
        if check_health(endpoint_type, nim_off_config):
            st.markdown('<p style="color:green; font-size:16px; text-align:left;">Status: 🟢</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:red; font-size:16px; text-align:left;">Status: 🔴</p>', unsafe_allow_html=True)
    with col5:
        if st.session_state.nv_stack_off_db_ready:
            st.markdown(f'<p style="color:green; font-size:16px; text-align:left;">DB ready: 🟢 </p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:red; font-size:16px; text-align:left;">DB ready: 🔴</p>', unsafe_allow_html=True)

with col2:
    col3, _, col4, col5 = st.columns([3, 2, 1, 2])
    with col3:
        st.write("NeMo Retriever-ON with NIM-ON")
    with col4:
        if check_health(endpoint_type, nim_on_config):
            st.markdown('<p style="color:green; font-size:16px; text-align:left;">Status: 🟢</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:red; font-size:16px; text-align:left;">Status: 🔴</p>', unsafe_allow_html=True)
    with col5:
        if st.session_state.nv_stack_on_db_ready:
            st.markdown(f'<p style="color:green; font-size:16px; text-align:left;">DB ready: 🟢 </p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:red; font-size:16px; text-align:left;">DB ready: 🔴</p>', unsafe_allow_html=True)

for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    if role == "user":
        with col1:
            with st.chat_message(role):
                st.markdown(content)
        with col2:
            with st.chat_message(role):
                st.markdown(content)
    elif role == "NIMOFF":
        with col1:
            with st.chat_message("assistant"):
                st.markdown(content)
    elif role == "NIM":
        with col2:
            with st.chat_message("assistant"):
                st.markdown(content)

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with col1:
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            messages = [{"role": "assistant" if m["role"] == "NIMOFF" else m["role"], "content": m["content"]} for m in st.session_state.messages if m["role"] in ["user", "NIMOFF"]]
            messages[-1]["content"] = get_prompt_with_context(prompt, oss_retriever_client)
            stream = get_os_stream_response(endpoint_type, nim_off_config, messages[-3:])
            response = st.write_stream(stream)
            if len(response) > 0:
                itl = sum(nim_off_time_to_next_token)
                nim_off_tokens_received = len(tokenizer([response])['input_ids'][0])
                metrics = "Received: " +  "{:.0f}".format(nim_off_tokens_received) +  " tokens"  + "\tITL: " + "{:.2f}".format(itl) + " seconds"
                nim_off_throughput = nim_off_tokens_received/itl
                st.markdown(f'''`{metrics}`''')
    st.session_state.messages.append({"role": "NIMOFF", "content": response})

    with col2:
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            messages = [{"role": "assistant" if m["role"] == "NIM" else m["role"], "content": m["content"]}for m in st.session_state.messages if m["role"] in ["user", "NIM"]]
            messages[-1]["content"] = get_prompt_with_context(prompt, nv_retriever_client)
            stream = get_nim_stream_response(endpoint_type, nim_on_config, messages[-3:])
            response = st.write_stream(stream)
            if len(response) > 0:
                itl = sum(nim_on_time_to_next_token)
                nim_on_tokens_received = len(tokenizer([response])['input_ids'][0])
                nim_on_throughput = nim_on_tokens_received/itl
                perf_gain = nim_on_throughput/nim_off_throughput
                metrics = "Received: " +  "{:.0f}".format(nim_on_tokens_received) +  " tokens"  + "\tITL: " + "{:.2f}".format(itl) + " seconds"
                st.markdown(f'''`{metrics}`''')
                gain = "Perf gain: "+"{:.1f}".format(perf_gain) + "X🚀"
                st.markdown(f'''**{gain}**''')
    st.toast("Complete")
    st.session_state.messages.append({"role": "NIM", "content": response})
