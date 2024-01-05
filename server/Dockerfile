FROM node:18.17
WORKDIR /usr/src/app/server
COPY server/package*.json ./
RUN npm install
COPY server/ ./
WORKDIR /usr/src/app/client
COPY client/ ./
WORKDIR /usr/src/app/server
EXPOSE 5000
CMD [ "node", "app.js" ]