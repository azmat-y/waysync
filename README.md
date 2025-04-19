# Introduction
WayClipSync enables clipboard sharing between guest and host in
wayland environments using wl-clipboard.

## Why
Clipboard sharing between guest and host does not work under a wayland
session with `virt-manager`, `spice-vdagent` only handles the case for X-session.

## Note
This program uses wl-clipboard and therefore will not work without it.
You can install it from your package manager.

## Setup
First since the program makes use of a shared file across host and
guest, we need to add a shared directory.<br>
1. Enable shared memory in memory menu of the guest.
2. Go to Hardware details > Add Hardware > Filesystem<br>
   Driver: virtiofs <br>
   source  path: src<br>
   target path: tag<br>
3. In guest VM<br>
   Add this line in /etc/fstab<br>
   `tag /home/user/mountpoint virtiofs rw, relatime 0 0`
4. In Host: Setup repository and autostart files<br>
   It is straightforward to install dependencies on the system itself<br>
   ```
   pip install watchdog
   git clone https://github.com/azmat-y/WayClipSync.git
   cd WayClipSync
   cp clipshare.desktop $HOME/.config/autostart/
   ```
   **IMP** For some reason using the autostart doesn't work. Instead of that we can manually run the program on both the host and guest machine like this
   ```
   cd WayClipSync
   python main.py $HOME/user/mountpoint/clipboard.txt
   ```
   Ensure that you edit out `<user>` from the desktop entry and that the paths
   are correct.
5. Now do the same thing for the guest.
6. Reboot the machine.
