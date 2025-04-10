FROM nginx:alpine

COPY index.html /usr/share/nginx/html/

RUN apk update
RUN apk add curl

