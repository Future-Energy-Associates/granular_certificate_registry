FROM node:20-bullseye-slim

WORKDIR /app

COPY ./package.json ./package.json
COPY ./package-lock.json ./package-lock.json
COPY ./webpack.config.js ./webpack.config.js

COPY ./src ./src
RUN npm install

# Baked into the bundle by webpack. Omit the argument to keep the
# localhost fallback in frontend/src/api/baseAPI.js.
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL
RUN npm run build

EXPOSE 8080

RUN npm install -g serve

CMD ["serve", "-s", "dist", "-l", "8080", "--single", "-C"]