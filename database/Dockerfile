# PostgreSQL Dockerfile for Battle Card Game
FROM postgres:16

# Set environment variables
ENV POSTGRES_DB=battlecards
ENV POSTGRES_USER=gameuser
ENV POSTGRES_PASSWORD=gamepassword

# Copy initialization scripts  
COPY ./database/*.sql /docker-entrypoint-initdb.d/

# Expose PostgreSQL port
EXPOSE 5432

# Create volume for data persistence
VOLUME ["/var/lib/postgresql/data"]

# Use the default postgres entrypoint