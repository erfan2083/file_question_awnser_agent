# --- Stage 1: Build ---
# Use an official Node.js image
FROM node:18-alpine AS build

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build the React app for production
RUN npm run build

# --- Stage 2: Serve ---
# Use a lightweight Nginx image
FROM nginx:1.25-alpine

# Copy the built static files from the 'build' stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy the nginx config file
# We don't have one, so Nginx will use its default, which is fine
# for serving index.html.

# Expose port 80 (Nginx default)
EXPOSE 80

# The default Nginx command will start the server
CMD ["nginx", "-g", "daemon off;"]