FROM node:20-alpine

WORKDIR /app

# Copy package files and prisma directory
COPY package*.json ./
COPY prisma ./prisma/

# Install dependencies
RUN npm install

# Generate Prisma client
RUN npx prisma generate

# Copy the rest of the application code
COPY . .

# Build TypeScript code
RUN npm run build

# Expose port
EXPOSE 5000

# Start the server using the compiled JS
CMD ["npm", "start"]
