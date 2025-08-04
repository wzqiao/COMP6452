# Use Node.js 22.16 as the base image
FROM node:22.16-alpine

# Set the working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Clean npm cache and install dependencies
RUN npm cache clean --force && \
    rm -rf node_modules && \
    npm install

# Copy application code
COPY . .

# Expose port 5173 (Vite default port)
EXPOSE 5173

# Start the development server with host binding
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]