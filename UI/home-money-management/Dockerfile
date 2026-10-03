FROM node:lts-alpine3.23 AS builder

# Set the working directory in the container to /app
WORKDIR /app

# Copy package.json and package-lock.json into the directory
COPY package*.json ./

# Install any needed packages specified in package.json
RUN npm ci

# Bundle app source inside Docker image (by copying from the local dev environment)
COPY . .

# Build the app for production
RUN npm run build

# Use a smaller, secure base image for the runtime
# alpine3.24, not 3.23: nginx:stable on 3.23 carries 38 OS HIGH/CRIT CVEs
# (libssl3, libcrypto3, curl, pcre2). The same tag on 3.24 scans to 2.
FROM nginx:stable-alpine3.24

# Copy the pre-built app from the previous stage
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for the app
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]
