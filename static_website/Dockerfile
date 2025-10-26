FROM  node:16-alpine

ENV NODE_ENV=production

WORKDIR /usr/src/lmao


COPY package.json .
COPY package-lock.json .

RUN npm install

COPY . .

CMD  node server.js
EXPOSE 3003
