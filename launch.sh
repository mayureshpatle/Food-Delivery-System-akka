#!/bin/sh

#build restaurant image

docker build -t restaurant-service Restaurant/

#build wallet image
docker build -t wallet-service Wallet/

#create restaurant container
docker run -p 8080:8080 --rm --name restaurant -v "$PWD/Restaurant/initialData.txt":/initialData.txt restaurant-service &

#create wallet container
docker run -p 8082:8080 --rm --name wallet -v "$PWD/Wallet/initialData.txt":/initialData.txt wallet-service &

#switch to Delivery folder
cd Delivery

#compile the akka project
mvn compile

#run the akka project by passing
#the filename as commandline argument
mvn exec:java -Dexec.args="./initialData.txt"