FROM node:20-bullseye-slim

WORKDIR /app

ENV REACT_APP_API_URL=https://api-640576971908.us-east1.run.app

COPY ./package.json ./package.json
COPY ./package-lock.json ./package-lock.json
COPY ./webpack.config.js ./webpack.config.js

COPY ./src ./src
RUN npm install
RUN npm run build

EXPOSE 8080

RUN npm install -g serve

CMD ["serve", "-s", "dist", "-l", "8080", "--single", "-C"]