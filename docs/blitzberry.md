# BlitzLoop on a Raspberry Pi

BlitzLoop can be installed on a Raspberry Pi, for what might possibly be the
world's smallest and cheapest full-featured karaoke box.

Normally, BlitzLoop runs on OpenGL on GLX on Xorg, and uses mpv with the
opengl-cb backend. The Raspberry Pi does not work efficiently with this setup.
However, BlitzLoop also supports a native Raspberry Pi backend, which uses EGL
directly without Xorg, and takes advantage of the hardware compositor to display
karaoke lyrics on a layer above the video playback layer, provided by mpv's rpi
backend. This guide focuses on this specific Raspberry Pi support.

## Prerequisites

* Raspberry Pi 3
* Arch Linux ARM

BlitzLoop has only been tested on a Raspberry Pi 3. Previous models may not be
powerful enough to work properly. Feel free to try.

## Installation

### Base OS

Follow the [Arch Linux ARM installation guide](https://archlinuxarm.org/platforms/armv8/broadcom/raspberry-pi-3)
for Raspberry Pi 3 (32bit version).

It is assumed that you are using the default `alarm` user to run BlitzLoop.
Additionally, you might want to change the password for `alarm` and/or `root`,
set up SSH keys, etc.

Make sure your Ethernet network is properly configured and you have internet
access (Arch Linux ARM uses DHCP by default), at least during installation.
We will be using WiFi as an AP for the client remote control devices to connect
to; it is possible to configure WiFi as a client to an existing network, but
that is beyond the scope of this guide.

This guide assumes that you have `sudo` installed and configured. If you don't,
run the commands prefixed with `sudo` as root (e.g. `su`).

### Set boot options

```shell
cat <<EOF | sudo tee /boot/config.txt > /dev/null
gpu_mem=256
disable_overscan=1
dtparam=audio=on
EOF
```

Also set the CPU frequency scaling policy to `performance` (otherwise rendering
FPS will randomly vary):

```shell
cat <<EOF | sudo tee /etc/tmpfiles.d/10-fast-cpu.conf
w /sys/devices/system/cpu/cpufreq/policy0/scaling_governor - - - - performance
EOF
```

Reboot.

### Configure environment

Set the locale to something with UTF-8:

```shell
echo 'en_US.UTF-8 UTF-8' | sudo tee /etc/locale.gen
sudo locale-gen
echo 'LANG=en_US.UTF-8' | sudo tee /etc/locale.conf
```

Grant `alarm` audio access and real-time priority for JACK:

```shell
sudo usermod -aG audio alarm
echo 'alarm - rtprio 99' | sudo tee -a /etc/security/limits.conf
```

Log out and back in.

### Update system

```shell
sudo pacman -Syu
```

### Install dependencies and BlitzLoop

We need a bunch of dependencies from AUR, which will be a lot easier to do with
yaourt:

```shell
# Manually pull in jack2 instead of jack, which works better here
sudo pacman -S --needed base-devel jack2 alsa-tools alsa-utils wget

mkdir -p ~/pkg; cd ~/pkg
wget https://aur.archlinux.org/cgit/aur.git/snapshot/package-query.tar.gz
tar xvzf package-query.tar.gz
cd ~/pkg/package-query
MAKEFLAGS="-j4" makepkg --skippgpcheck --syncdeps
sudo pacman -U package-query-*.pkg.tar.xz

cd ~/pkg
wget https://aur.archlinux.org/cgit/aur.git/snapshot/yaourt.tar.gz
tar xvzf yaourt.tar.gz
cd ~/pkg/yaourt
MAKEFLAGS="-j4" makepkg --skippgpcheck --syncdeps
sudo pacman -U package-query-*.pkg.tar.xz

cd ~/pkg
yaourt -S mpv-rpi
yaourt -S blitzloop-git
```

### Configure BlitzLoop

```shell
mkdir -p ~/.config/blitzloop
cat <<EOF >~/.config/blitzloop/blitzloop.conf
display=rpi
mpv-vo=rpi
EOF
```

### Get songs

Put your songs in `/home/alarm/.local/share/blitzloop/songs/` (create it first).

### Test out BlitzLoop

Run:

```shell
cd ~
blitzloop --mpv-ao=alsa --no-audioengine
```

Connect to TCP port 10111 and check to see if everything works properly.
Note that you will not have any microphone support at this point, as the
Raspberry Pi has no audio input.

If you have no audio, you may need to run `amixer cset numid=3 2`.

## Systemd service

```shell
cat >~/startblitz.sh <<EOF
#!/bin/sh
cd "\$(dirname "\$0")"
amixer cset numid=3 2
python -u /usr/bin/blitzloop --port=80 --no-audioengine --mpv-ao=alsa
EOF
chmod +x ~/startblitz.sh

cat <<EOF | sudo tee /etc/systemd/system/blitzloop.service > /dev/null
[Unit]
Description=BlitzLoop

[Service]
Type=simple
User=alarm
Group=alarm
ExecStart=/home/alarm/startblitz.sh
AmbientCapabilities=CAP_NET_BIND_SERVICE
LimitRTPRIO=99
LimitMEMLOCK=1024000000

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable blitzloop
sudo systemctl start blitzloop
```

## Mic setup

To get microphones supported, you will need to configure JACK. If you have a
single USB sound card you want to use for input/output, do something like this
in `~/startblitz.sh`:

```shell
cd "$(dirname "$0")"
export JACK_NO_AUDIO_RESERVATION=1
jackd -R --timeout 10000 -d alsa -P hw:AUDIO -r 48000 -p 240 -n 2 -o 2 &
jack_pid=$!
alsa_in -j mic -d hw:Receiver -c 2 -p 240 -n 2 -q 0 &
alsa_pid=$!
trap "kill $jack_pid $alsa_pid" TERM INT
sleep 1
python -u /usr/bin/blitzloop --port=80 --mpv-ao=jack
```

Where `hw:1` is your desired audio device (you can look in `/proc/asound/cards`
for symbolic names you can use instead of index numbers which may change,
and use them as e.g. `hw:AUDIO`).

If you have separate cards for input/output (e.g. you want to use built-in or
HDMI audio for output, or have a separate USB microphone and sound card), try
something like this:

```shell
cd "$(dirname "$0")"
ulimit -a
export JACK_NO_AUDIO_RESERVATION=1
jackd -R --timeout 10000 -d alsa -P hw:AUDIO -r 48000 -p 240 -n 2 -o 2 &
jack_pid=$!
alsa_in -j mic -d hw:Receiver -c 2 -p 240 -n 2 -q 0 &
alsa_pid=$!
trap "kill $jack_pid $alsa_pid" TERM INT
sleep 2
python -u /usr/bin/blitzloop --port=80 --mpv-ao=jack --mics=mic:capture_1,mic:capture_2 "$@"
```

## WiFi setup

Set up a WiFi hotspot for tablets to connect to:

```shell
sudo pacman -S --needed dnsmasq hostapd iptables

cat <<EOF | sudo tee /etc/hostapd/hostapd.conf >/dev/null
interface=wlan0
ssid=BlitzLoop
hw_mode=g
channel=6
wmm_enabled=1
EOF
sudo systemctl enable hostapd
sudo systemctl start hostapd

cat <<EOF | sudo tee /etc/dnsmasq.conf >/dev/null
no-resolv
server=8.8.8.8
address=/blitz/192.168.42.1
address=/bl/192.168.42.1
address=/b/192.168.42.1
interface=wlan0
dhcp-range=192.168.42.100,192.168.42.200,12h
EOF

sudo systemctl enable dnsmasq
sudo systemctl start dnsmasq

cat <<EOF | sudo tee /etc/systemd/network/hostap.network >/dev/null
[Match]
Name=wlan0

[Network]
Address=192.168.42.1/24
IPMasquerade=yes
EOF

sudo systemctl restart systemd-networkd.service
```

Now you can connect to the `BlitzLoop` SSID and browse to http://b/.

## Limitations / known bugs

Audio processing already uses most of one core by default. Changing the speed
or tempo in certain ways causes increased CPU usage and drop-outs.
