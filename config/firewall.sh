#!/bin/bash
echo Setting firewall rules...

###### Debut Initialisation ######

# Reject all connect input
iptables -t filter -P INPUT DROP
iptables -t filter -P FORWARD DROP
echo - All connect input is forbidden : [OK]

# Reject all output connect
iptables -t filter -P OUTPUT DROP
echo - All connect output is forbidden : [OK]

# Flush all rules
iptables -t filter -F
iptables -t filter -X
echo - flush rules : [OK]

# SMTP protect
iptables -N LOG_REJECT_SMTP
iptables -A LOG_REJECT_SMTP -j LOG --log-prefix ' SMTP REJECT PAQUET : '
iptables -A LOG_REJECT_SMTP -j DROP
echo - Protect SMTP

# Ne pas casser les connexions etablies
iptables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
echo - Keep connected : [OK]

# Allow DNS, FTP, HTTP, NTP request
iptables -t filter -A OUTPUT -p tcp --dport 21 -j ACCEPT
iptables -t filter -A OUTPUT -p tcp --dport 80 -j ACCEPT
iptables -t filter -A OUTPUT -p tcp --dport 53 -j ACCEPT
iptables -t filter -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -t filter -A OUTPUT -p udp --dport 123 -j ACCEPT


iptables -t filter -A INPUT -p tcp --dport 80 -j ACCEPT
echo - Allow HTTP

# Allow SMTP request
iptables -A OUTPUT -p tcp --dport 25  -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -p tcp --sport 25  -m state --state ESTABLISHED,RELATED -j ACCEPT
echo - Allow SMTP : [OK]

# Allow loopback
iptables -t filter -A INPUT -i lo -j ACCEPT
iptables -t filter -A OUTPUT -o lo -j ACCEPT
echo - Allow loopback : [OK]

# Allow ping
iptables -t filter -A INPUT -p icmp -j ACCEPT
iptables -t filter -A OUTPUT -p icmp -j ACCEPT
echo - Allow ping : [OK]

# Allow SSH
iptables -t filter -A INPUT -p tcp --dport 6060 -m recent --rcheck --seconds 60 --hitcount 2 --name SSH -j LOG --log-prefix "SSH REJECT"

 iptables -t filter -A INPUT -p tcp --dport 6060 -m recent --update --seconds 60 --hitcount 2 --name SSH -j DROP

iptables -t filter -A INPUT -p tcp --dport 6060 -m state --state NEW -m recent --set --name SSH -j ACCEPT
