docker run -it `
  --name n8n `
  -p 5678:5678 `
  -e GENERIC_TIMEZONE="Asia/Kolkata" `
  -e TZ="Asia/Kolkata" `
  -v n8n_data:/home/node/.n8n `
  docker.n8n.io/n8nio/n8n