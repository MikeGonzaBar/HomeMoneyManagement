# Use an official Node runtime as the base image
FROM node:current-alpine

# Set the working directory in the container to /app
WORKDIR /app

# Copy package.json and package-lock.json into the directory
COPY package*.json ./

# Install any needed packages specified in package.json
RUN npm install

# Bundle app source inside Docker image (by copying from the local dev environment)
COPY . .

# Build the app for production
RUN npm run build

# Use a smaller, secure base image for the runtime
FROM nginx:stable-alpine3.17

# Copy the pre-built app from the previous stage
COPY --from=0 /app/dist /usr/share/nginx/html

# Expose port 80 for the app
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]