FROM ubuntu:20.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Apache, PHP, SSH, and networking tools
RUN apt-get update && \
    apt-get install -y apache2 php libapache2-mod-php openssh-server sudo \
                       net-tools iproute2 curl vim nano && \
    apt-get clean && \
    apt install gcc -y && \
    rm -rf /var/lib/apt/lists/*

# Enable Apache modules
RUN a2enmod rewrite ssl php7.4

RUN echo 'root:Password123!' | chpasswd

# Configure SSH
RUN mkdir /var/run/sshd && \
    echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config && \
    echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config && \
    sed -i 's/#Port 22/Port 22/' /etc/ssh/sshd_config

# Create Arlen Service Center themed users
RUN useradd -m -s /bin/bash propane_tech && echo 'propane_tech:sweetlady' | chpasswd && \
    useradd -m -s /bin/bash strickland && echo 'strickland:propane123' | chpasswd && \
    useradd -m -s /bin/bash mechanic && echo 'mechanic:automotive' | chpasswd

# Copy website files
COPY website/ /var/www/html/

# Set proper permissions
RUN chown -R www-data:www-data /var/www/html && \
    chmod -R 755 /var/www/html

# Make /usr/bin/passwd SUID-root for Dirty COW demo
RUN chmod u+s /usr/bin/passwd

RUN echo "su root" >> /home/strickland/.bash_history
RUN echo "Password123! ^C" >> /home/strickland/.bash_history
RUN echo "su root" >> /home/strickland/.bash_history
RUN echo "Password123!" >> /home/strickland/.bash_history

RUN echo "su root" >> /home/propane_tech/.bash_history
RUN echo "Password123! ^C" >> /home/propane_tech/.bash_history
RUN echo "su root" >> /home/propane_tech/.bash_history
RUN echo "Password123!" >> /home/propane_tech/.bash_history

RUN echo "su root" >> /home/mechanic/.bash_history
RUN echo "Password123! ^C" >> /home/mechanic/.bash_history
RUN echo "su root" >> /home/mechanic/.bash_history
RUN echo "Password123!" >> /home/mechanic/.bash_history


# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose ports
# --- KotH tag target. This file is intentionally writable by whoever
# controls this box (that's the game) -- but nothing running IN this
# container ever reports its contents. See reporter-sidecar/. ---
RUN mkdir -p /opt/koth && echo "unclaimed" > /opt/koth/tag && chmod 666 /opt/koth/tag
EXPOSE 80 22

# Start services
CMD ["/bin/bash", "-c", "if [ -f /start.sh ]; then /start.sh; else tail -f /dev/null; fi"]
