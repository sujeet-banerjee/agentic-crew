docker-config down -f docker-compose-codespace.yml 
docker-compose down -f docker-compose-codespace.yml 
docker-compose -f docker-compose-codespace.yml down
docker-compose -f docker-compose-codespace.yml up -d
docker logs -f litellm_proxy
docker ps
docker logs -f litellm_proxy
echo $OPENAI_API_KEY
docker-compose -f docker-compose-codespace.yml down
