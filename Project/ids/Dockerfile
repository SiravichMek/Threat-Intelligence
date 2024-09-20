# Dockerfile for Suricata IDS
FROM ubuntu:20.04

# Install Suricata and other necessary packages
RUN apt-get update && \
    apt-get install -y suricata

# Expose log directory
VOLUME /var/log/suricata

CMD ["suricata", "-c", "/etc/suricata/suricata.yaml", "-i", "eth0"]
