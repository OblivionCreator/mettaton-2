docker prune
docker build -t mettaton-2 .
docker save mettaton-2 -o ~/docker-store/mettaton-2.tar