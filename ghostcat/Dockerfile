FROM ubuntu:18.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Java, wget, networking tools, SSH, and sudo
RUN apt-get update && \
    apt-get install -y default-jdk wget iproute2 net-tools openssh-server sudo && \
    apt-get clean && \
    apt install iputils-ping -y && \
    apt install nmap -y && \
    rm -rf /var/lib/apt/lists/*

# Download and install a specific vulnerable Tomcat version
RUN cd /tmp && \
    wget https://archive.apache.org/dist/tomcat/tomcat-9/v9.0.30/bin/apache-tomcat-9.0.30.tar.gz && \
    tar xzf apache-tomcat-9.0.30.tar.gz && \
    mv apache-tomcat-9.0.30 /usr/share/tomcat9 && \
    rm apache-tomcat-9.0.30.tar.gz

# Create necessary directories and set up Tomcat structure
RUN mkdir -p /usr/share/tomcat9/conf && \
    mkdir -p /usr/share/tomcat9/temp && \
    mkdir -p /var/lib/tomcat9/webapps && \
    ln -sf /usr/share/tomcat9/webapps /var/lib/tomcat9/webapps

# Copy configuration files
COPY server.xml /usr/share/tomcat9/conf/server.xml
COPY tomcat-users.xml /usr/share/tomcat9/conf/tomcat-users.xml

COPY webapp/ /usr/share/tomcat9/webapps/ROOT/

# Configure SSH
RUN mkdir /var/run/sshd && \
    echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config && \
    echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config && \
    sed -i 's/#Port 22/Port 22/' /etc/ssh/sshd_config

# Configure dangerous sudo permissions for privilege escalation
RUN echo 'bill ALL=(root) NOPASSWD: /usr/bin/awk' >> /etc/sudoers

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose ports
# --- KotH tag target. This file is intentionally writable by whoever
# controls this box (that's the game) -- but nothing running IN this
# container ever reports its contents. See reporter-sidecar/. ---
RUN mkdir -p /opt/koth && echo "unclaimed" > /opt/koth/tag && chmod 666 /opt/koth/tag
EXPOSE 8009 8080 22

# Start Tomcat with routing
CMD ["/bin/bash", "-c", "if [ -f /start.sh ]; then /start.sh; else tail -f /dev/null; fi"]
