# frontend/Dockerfile

# 1. Use an official Node.js runtime
FROM node:20-alpine

# 2. Set working directory
WORKDIR /app

# 3. Copy package.json and lock file
COPY package*.json ./

# 4. Install dependencies
RUN npm install

# 5. Copy the rest of the app's source code
COPY . .

# 6. Build the Next.js app
RUN npm run build

# 7. Expose port and start the app
EXPOSE 3000
CMD ["npm", "start"]