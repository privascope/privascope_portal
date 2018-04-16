FROM ubuntu
RUN apt-get update && apt-get install -y curl
RUN mkdir /usr/src/app
WORKDIR /usr/src/app
COPY . /usr/src/app
CMD sh ./access-resource.sh 
