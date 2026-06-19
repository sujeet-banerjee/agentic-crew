# agentic-crew

What would be the best way to have the minions work right within your laptop, and work with the like agents running elsewhere?





#### Locate

1\. The workflows/ folder:

Whenever you build an awesome agentic workflow in the n8n UI, you can click "Download" in n8n. This exports a JSON file. By saving them in this folder, you version-control your curriculum. The students can simply clone the repo, open n8n, and click "Import from File" to instantly have your exact workflow.



2\. The config/ folder:

Because we are using LiteLLM as an API gateway/MLOps layer, it requires a config.yaml file to tell it where Ollama is and how to track costs. Keeping configs out of the root directory keeps the repo clean. (Note: you'd map this in your compose file like: - ./config/litellm/config.yaml:/app/config.yaml)



3\. The notebooks/ folder:

Since RAGAS and standard ML-evaluations are heavily Python-based, this acts as the "Code Sandbox." we provide a requirements.txt so students can set up their local Python environment (or a virtual environment) and immediately start running the Jupyter notebooks against the Docker containers.



4\. The data/ folder \& .gitignore:

If you change your docker-compose.yml to use bind mounts instead of named volumes (e.g., ./data/postgres\_data:/var/lib/postgresql/data), all the database data saves directly into this folder.

Crucial Step: You must put data/ in your .gitignore file. You do not want to accidentally push gigabytes of Postgres databases, Qdrant vectors, or Redis memory logs to GitHub!





#### Run

###### Start containers:

docker-compose up -d



###### Python Scripts Runs:

* When you clone this repo, duplicate the .env.example file, rename the copy to .env, and fill in your actual passwords and keys.
* Create a virtual ENV for python installs, and switch to the Virtual-env:
     python -m venv ai\_env
     source ai\_env/bin/activate  # Windows: ai\_env\\Scripts\\activate
     pip install langchain langchain-openai langgraph ragas pandas datasets psycopg psycopg-pool streamlit

&#x20;       pip install --upgrade ragas langchain-community langchain langchain-openai
     



* 

