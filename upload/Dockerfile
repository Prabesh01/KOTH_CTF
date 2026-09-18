FROM ubuntu:18.04

# Set timezone to prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/New_York

# Install Apache, PHP, Python3, and networking tools
RUN apt-get update && \
    apt-get install -y tzdata && \
    apt-get install -y apache2 php libapache2-mod-php python3 iproute2 net-tools openssh-server && \
    a2enmod php7.2 && \
    mkdir -p /run/sshd

# Copy website files and startup script
COPY website/ /var/www/html/
COPY start.sh /start.sh

# Create uploads directory and set permissions
RUN mkdir -p /var/www/html/uploads && \
    chmod 777 /var/www/html/uploads && \
    chown -R www-data:www-data /var/www/html/ && \
    chmod +x /start.sh

# Create King of the Hill themed users
RUN useradd -m -s /bin/bash minh && echo 'minh:ocean_walker' | chpasswd && \
    useradd -m -s /bin/bash connie && echo 'connie:violin_prodigy' | chpasswd && \
    useradd -m -s /bin/bash buckley && echo 'buckley:angel' | chpasswd

# Expose ports 80 (main service) and 8080 (hidden King of the Hill service)
# --- KotH tag target. This file is intentionally writable by whoever
# controls this box (that's the game) -- but nothing running IN this
# container ever reports its contents. See reporter-sidecar/. ---
RUN mkdir -p /opt/koth && echo "unclaimed" > /opt/koth/tag && chmod 666 /opt/koth/tag
EXPOSE 80 8080 22

# Start with custom script
CMD ["/bin/bash", "-c", "service ssh start; if [ -f /start.sh ]; then /start.sh; else tail -f /dev/null; fi"]
