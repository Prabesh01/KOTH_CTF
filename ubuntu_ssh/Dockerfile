FROM ubuntu:20.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install SSH, Telnet, cron and networking tools
RUN apt-get update && \
    apt-get install -y openssh-server telnetd xinetd cron iproute2 net-tools && \
    mkdir /var/run/sshd

# Configure SSH
RUN echo 'root:toor' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Create second SSH config for port 2222
COPY sshd_config_2222 /etc/ssh/sshd_config_2222

# Create King of the Hill themed users
RUN useradd -m -s /bin/bash strickland && echo 'strickland:sweet_lady_propane' | chpasswd && \
    useradd -m -s /bin/bash joe_jack && echo 'joe_jack:mechanic' | chpasswd && \
    useradd -m -s /bin/bash enrique && echo 'enrique:megalo_mart' | chpasswd

# Set up vulnerable cron job for privilege escalation
RUN mkdir -p /opt/scripts && \
    echo '#!/bin/bash' > /opt/scripts/backup.sh && \
    echo 'echo "Running backup at $(date)"' >> /opt/scripts/backup.sh && \
    echo 'tar -czf /tmp/backup_$(date +%Y%m%d_%H%M%S).tar.gz /home/* 2>/dev/null' >> /opt/scripts/backup.sh && \
    chmod 755 /opt/scripts/backup.sh && \
    chown root:root /opt/scripts/backup.sh && \
    chmod 777 /opt/scripts && \
    echo '#!/bin/bash' > /opt/scripts/runner.sh && \
    echo 'while true; do' >> /opt/scripts/runner.sh && \
    echo '  /opt/scripts/backup.sh' >> /opt/scripts/runner.sh && \
    echo '  sleep 10' >> /opt/scripts/runner.sh && \
    echo 'done' >> /opt/scripts/runner.sh && \
    chmod 755 /opt/scripts/runner.sh && \
    chown root:root /opt/scripts/runner.sh && \
    echo '@reboot root nohup /opt/scripts/runner.sh > /dev/null 2>&1 &' >> /etc/crontab

# Expose ports
# --- KotH tag target. This file is intentionally writable by whoever
# controls this box (that's the game) -- but nothing running IN this
# container ever reports its contents. See reporter-sidecar/. ---
RUN mkdir -p /opt/koth && echo "unclaimed" > /opt/koth/tag && chmod 666 /opt/koth/tag
EXPOSE 22 2222 23

# Start services
COPY start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/bin/bash", "-c", "if [ -f /start.sh ]; then /start.sh; else tail -f /dev/null; fi"]
