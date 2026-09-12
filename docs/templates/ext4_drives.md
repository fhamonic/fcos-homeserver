# `ext4_drives`

List of ext4-formatted storage devices to be automatically mounted when available.

Each drive gets a systemd mount unit with `nofail` and automount, so a missing or late drive never blocks the boot, and an SELinux context that lets rootless containers read and write it.

## `ext4_drives[].uuid`

The UUID of the block device to mount.
It uniquely identifies a filesystem on a specific partition (i.e. a block device).

You can use:

```bash
lsblk
```

to list connected block devices and partitions, then, replacing `xxx` as appropriate:

```bash
sudo blkid /dev/xxx
```

to obtain the UUID of the desired filesystem.

* **Type:** String
* **Purpose:** Ensures consistent device identification across reboots.

## `ext4_drives[].mount_point`

Filesystem path where the drive will be mounted.

On FCOS, the root filesystem is immutable and writable storage is limited to `/var`.
For this reason, mount points **must** reside under `/var`.

* **Type:** Absolute path
* **Example:** `/var/hdd`

## `ext4_drives[].placeholder_dirs`

Directories to be created under the mount point on the host system.

These directories act as placeholders when the device is not present at boot, allowing containers that bind-mount these paths to start normally.
If the device becomes available later, it will be mounted automatically and its contents will transparently shadow the placeholder directories.

* **Type:** List of directory names
* **Purpose:** Subdirectories of the mounted drive for which placeholders should exist.
* **Examples:**
    * `Movies`
    * `Shows`
    * `Music`
    * `Photos`
