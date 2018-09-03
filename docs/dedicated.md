# BlitzLoop on a dedicated x86 box (with Arch Linux)

Normally, BlitzLoop runs on OpenGL on GLX on Xorg, and uses mpv with the
opengl-cb backend. However, for a dedicated system, it also supports a raw DRM
backend that runs without a windowing system or compositor. This guide focuses
on this mode, using Arch Linux as the base OS.

This guide is intended for x86 systems dedicated to BlitzLoop. However, feel
free to take whatever bits are useful to you and customize your setup. These
steps were tested on a LattePanda, but should work on basically any x86 box
with proper KMS support (i.e. Intel or AMD, and perhaps Nvidia with Nouveau).

## Prerequisites

* An x86-64 machine with modern KMS/DRM graphics (e.g. Intel GPU)
* Arch Linux x86-64

## Installation

### Base OS

Follow the [Arch Linux installation guide](https://wiki.archlinux.org/index.php/Installation_guide).

### Users and permissions

As root, add a user for BlitzLoop:

```shell
useradd -m blitz
```

The rest of this guide assumes you're running as the `blitz` user and uses
`sudo` to refer to commands to be run as root; you can grant sudo access to the
`blitz` user or use a separate root shell.

Grant `blitz` audio/video access and real-time priority for JACK:

```shell
sudo usermod -aG audio,video blitz
echo 'blitz - rtprio 99' | sudo tee -a /etc/security/limits.conf
```

### Configure environment

Set the locale to something with UTF-8:

```shell
echo 'en_US.UTF-8 UTF-8' | sudo tee /etc/locale.gen
sudo locale-gen
echo 'LANG=en_US.UTF-8' | sudo tee /etc/locale.conf
```

Log out and back in.

### Update system

```shell
sudo pacman -Syu
```

### LattePanda specific configuration

Skip this section if you're not using a LattePanda. However, if you need to
configure mixer controls, the last two commands may be useful on your platform
too.

To make the built-in audio work, a kernel command line argument is required.
You also need another argument to disable the (nonexistent) DSI panel.
Edit `/etc/default/grub` and set:
```shell
GRUB_CMDLINE_LINUX="snd_soc_rt5645.quirk=0x31 video=DSI-1:d"
```

Then update the config, fix up the ALSA UCM config, set the correct mixer
profile, and save the settings:

```shell
sudo grub-mkconfig -o /boot/grub/grub.cfg

# Symlink the ALSA UCM config files so alsaucm will find them.
A=AMICorporation-Defaultstring-Defaultstring-CherryTrailCR
C=chtrt5645
cd /usr/share/alsa/ucm/
sudo mkdir $A
sudo ln -s ../$C/HiFi.conf $A/HiFi.conf
sudo ln -s ../$C/$C.conf $A/$A.conf

# Set up the mixer controls as required
sudo alsaucm -c $C set _verb HiFi set _enadev Headphone

# This is useful on other platforms that need to store mixer controls too
sudo ln -s /usr/lib/systemd/system/alsa-restore.service /etc/systemd/system/multi-user.target.wants/
sudo alsactl store
```

Reboot for the changes to take effect. The system should now come up with
functional audio. The audio device name is `hw:chtrt5645`.

### Install dependencies and BlitzLoop

We need a bunch of dependencies from AUR, which will be a lot easier to do with
yaourt:

```shell
# Manually pull in jack2 instead of jack, which works better here
sudo pacman -S --needed base-devel jack2 alsa-tools alsa-utils wget git mpv libva-intel-driver

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
sudo pacman -U yaourt-*.pkg.tar.xz

cd ~/pkg
yaourt -S python-pympv-git # required until python-pympv-0.5.1 is in AUR
yaourt -S mpv-git # required until mpv-0.29.1 or later is released and in Arch
yaourt -S blitzloop-git
```

**TODO**: kms++ is a dependency too, get it into AUR

### Configure BlitzLoop

```shell
mkdir -p ~/.config/blitzloop
cat <<EOF >~/.config/blitzloop/blitzloop.conf
display=kms
EOF
```
### Get songs

Put your songs in `/home/blitz/.local/share/blitzloop/songs/` (create it first).

### Test out BlitzLoop

Run:

```shell
blitzloop --mpv-audio-device=alsa/hw:chtrt5645 --no-audioengine --mpv-extra="audio-format=s16"
```

Connect to TCP port 10111 and check to see if everything works properly.
Note that you will not have any microphone support at this point. You should use
the ALSA device short name instead of `chtrt5645`; check `/proc/asound/cards`
for a list. The `audio-format=s16` parameter is required to work around driver
issues in LattePanda, and should not be required on other systems (but it
probably won't hurt).

## Systemd service

This sets up the service with a separate input card for microphones. See
[blitzberry.md#mic-setup](blitzberry.md#mic-setup) for other options.

```shell
cat >~/startblitz.sh <<EOF
#!/bin/sh
cd "$(dirname "$0")"
export JACK_NO_AUDIO_RESERVATION=1
jackd -R --timeout 10000 -d alsa -P hw:chtrt5645 -r 48000 -p 240 -n 2 -o 2 -S &
jack_pid=$!
alsa_in -j mic -d hw:Receiver -c 2 -p 240 -n 2 -q 0 &
alsa_pid=$!
trap "kill $jack_pid $alsa_pid" TERM INT
sleep 2
python -u /usr/bin/blitzloop --port=80 --mpv-ao=jack --mics=mic:capture_1,mic:capture_2 "$@"
EOF
chmod +x ~/startblitz.sh

cat <<EOF | sudo tee /etc/systemd/system/blitzloop.service > /dev/null
[Unit]
Description=BlitzLoop

[Service]
Type=simple
User=blitz
Group=blitz
ExecStart=/home/blitz/startblitz.sh
AmbientCapabilities=CAP_NET_BIND_SERVICE
LimitRTPRIO=99
LimitMEMLOCK=1024000000

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable blitzloop
sudo systemctl start blitzloop
```

## WiFi setup

See [blitzberry.md#wifi-setup](blitzberry.md#wifi-setup).
