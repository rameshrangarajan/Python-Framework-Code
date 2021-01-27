FROM ubuntu:16.04

RUN apt-get update -y
RUN apt-get install python3-pip -y
RUN pip3 install --upgrade pip
RUN apt-get install imagemagick --yes
RUN sed -i 's/<policy domain="coder" rights="none" pattern="PDF" \/>/<policy domain="coder" rights="read|write" pattern="PDF" \/>/g' /etc/ImageMagick-6/policy.xml
RUN apt-get install -y unoconv

RUN apt-get install --yes curl
RUN curl --silent --location https://deb.nodesource.com/setup_10.x | bash -
RUN apt-get install --yes nodejs
RUN apt-get install --yes build-essential
RUN npm install elasticdump -g

WORKDIR /app
COPY . /app
RUN pip3 install -r ./flask_backend/req.txt




RUN python3 -m spacy download en --user
RUN python3 -m nltk.downloader all