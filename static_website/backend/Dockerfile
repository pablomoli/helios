FROM node:20-alpine

WORKDIR /usr/src/app

# Copy package files and install production dependencies
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Copy backend code
COPY . .

EXPOSE 5000

CMD ["node", "server.js"]
