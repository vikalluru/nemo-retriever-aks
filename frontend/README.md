Get nemo-retriever client from NGC

Create conda env

conda create -n frontend python=3.11

conda activate frontend

cd nvstack-aks/frontend

Export openai api key and hf key as environment variables

export OPENAI_API_KEY=<your api key>
export HUGGING_FACE_HUB_TOKEN=<your hf key>

Install requirements in the environment

pip install -r requirements.txt

Run frontend

streamlit run app.py