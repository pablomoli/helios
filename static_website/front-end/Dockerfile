# Stage 1: Build React app
FROM node:20-alpine AS build

WORKDIR /usr/src/app

# Copy frontend package files
COPY front-end/package.json front-end/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy the rest of frontend code
COPY front-end/. .

# Build React
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy build output
COPY --from=build /usr/src/app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
