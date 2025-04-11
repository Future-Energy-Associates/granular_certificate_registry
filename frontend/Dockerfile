FROM node:20-bullseye-slim

WORKDIR /app

ENV REACT_APP_API_URL=https://api-dot-rich-store-445612-c6.ew.r.appspot.com

COPY ./package.json ./package.json 
COPY ./package-lock.json ./package-lock.json 
COPY ./webpack.config.js ./webpack.config.js
COPY ./src ./src                      

RUN npm install

RUN npm run build

EXPOSE 8080

RUN npm install -g serve

CMD ["serve", "-s", "dist", "-l", "8080"]
