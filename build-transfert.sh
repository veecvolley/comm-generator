docker build -t veec-comm-generator:`cat VERSION.md` -f Dockerfile.prod .
docker save veec-comm-generator:`cat VERSION.md` -o /tmp/veec-comm-generator_`cat VERSION.md`.docker
scp -P 2222 /tmp/veec-comm-generator_`cat VERSION.md`.docker furyfly.fr:/tmp/