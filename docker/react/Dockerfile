FROM node:22-alpine AS node-builder

WORKDIR /app

ARG UID
ARG GID

# Create app user for security (don't run as root)
# the GROUP_NAME and USER_NAME is only valid in the RUN scope
RUN if getent group "$GID" > /dev/null 2>&1; then \
        GROUP_NAME=$(getent group "$GID" | cut -d: -f1); \
        echo "Group with GID $GID exists: $GROUP_NAME"; \
    else \
        GROUP_NAME=appgroup; \
        addgroup -g $GID $GROUP_NAME; \
        echo "Created group $GROUP_NAME with GID $GID"; \
    fi && \
    if getent passwd "$UID" > /dev/null 2>&1; then \
        USER_NAME=$(getent passwd "$UID" | cut -d: -f1); \
        echo "User with UID $UID exists: $USER_NAME"; \
    else \
        USER_NAME=appuser; \
        adduser -D -u $UID -G "$GROUP_NAME" -h /home/$USER_NAME $USER_NAME; \
        echo "Created user $USER_NAME with UID $UID"; \
    fi && \
    chown -R $USER_NAME:$GROUP_NAME /app


USER ${UID}:${GID}

# Expose development server port
EXPOSE 3000