# Introduction
waysync enables clipboard sharing between guest and host in
wayland environments using wl-clipboard.

## Why?
Clipboard sharing between guest and host does not work under a wayland
session with `virt-manager`, `spice-vdagent` only handles the case for X-session.

## Note
This program uses wl-clipboard and therefore will not work without it.
You can install it from your package manager.

## Setup
1. First, you need to configure firewall rules. I am using port 4444 here.
```
# Add port 4444 to the libvirt zone (where your VM traffic goes)
sudo firewall-cmd --zone=libvirt --add-port=4444/tcp --permanent

# Reload firewall rules
sudo firewall-cmd --reload

# Verify it was added
sudo firewall-cmd --zone=libvirt --list-all

```

If the above does not work, you can try adding the rule to public zone.
```
sudo firewall-cmd --zone=public --add-port=4444/tcp
```

2. Figure out IP of your host from the guest HOST_IP. 
```
# From guest
ip route | grep default 
# you want the first ip
# I will refer to this ip as HOST_IP
```

3. Clone on both host and guest and run.
```
git clone waysync

# on host 
python main.py server --port 4444

# on guest
python main.py client --host HOST_IP --port 4444
```
