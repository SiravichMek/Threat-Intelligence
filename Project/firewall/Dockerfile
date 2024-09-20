FROM ubuntu:latest

# Install UFW
RUN apt-get update && \
    apt-get install -y ufw && \
    apt-get clean

# Copy custom UFW configuration
COPY ufw.conf /etc/ufw/ufw.conf

# Set correct ownership and permissions for UFW config file
RUN chown root:root /etc/ufw/ufw.conf && \
    chmod 644 /etc/ufw/ufw.conf

# Create log directory and log file for UFW
RUN mkdir -p /var/log/ufw && \
    touch /var/log/ufw/ufw.log && \
    chmod 755 /var/log/ufw && \
    chown root:root /var/log/ufw/ufw.log && \
    chmod 644 /var/log/ufw/ufw.log


# Enable UFW and tail the log file to keep the container running
CMD ["sh", "-c", "ufw enable"]