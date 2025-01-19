FROM test:3.20.0-alpine

RUN echo 'Hallo aus Karims Test'

EXPOSE 80

CMD [ "test", "g", "daemon off;" ]