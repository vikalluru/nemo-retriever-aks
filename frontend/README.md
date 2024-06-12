# NVStack Frontend Setup Guide

Follow these steps to set up the NVStack frontend.

## Prerequisites

1. Ensure you have [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) installed on your machine.
2. Obtain the Nemo-retriever client from [NVIDIA GPU Cloud (NGC)](https://ngc.nvidia.com/).

## Step-by-Step Instructions

### 1. Create a Conda Environment

First, create a new Conda environment with Python 3.11:

```sh
conda create -n frontend python=3.11
```

Activate the newly created environment:

```sh
conda activate frontend
```

### 2. Navigate to the Frontend Directory

Change to the `nvstack-aks/frontend` directory:

```sh
cd nvstack-aks/frontend
```

### 3. Export API Keys

Export your OpenAI API key and Hugging Face Hub token as environment variables:

```sh
export OPENAI_API_KEY=<your_openai_api_key>
export HUGGING_FACE_HUB_TOKEN=<your_hf_token>
```

Replace `<your_openai_api_key>` and `<your_hf_token>` with your actual API keys.

### 4. Install Requirements

Install the required Python packages in your environment:

```sh
pip install -r requirements.txt
```

### 5. Run the Frontend

Run the Streamlit application:

```sh
streamlit run app.py
```

Your NVStack frontend should now be up and running. Open the URL provided by Streamlit in your browser to interact with the application.

---

Feel free to modify the instructions based on any additional requirements or changes specific to your project.