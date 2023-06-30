import os
import stat
import collections
import psutil
import logging
import glob


def path_stat(path, logger=None):
    try:
        s_obj = os.stat(path)
        modes = {k: getattr(stat, k) for k in dir(stat) if k.startswith(('S_IS', 'S_IMODE', 'S_IFMT', 'filemode')) and callable(getattr(stat, k))}
        modes = {k: v(s_obj.st_mode) for k, v in modes.items()}
        props = {k: getattr(stat, k) for k in dir(stat) if k.startswith(('ST_', )) and isinstance(getattr(stat, k), int)}
        props = {k: s_obj[v] for k, v in props.items()}
        return {**modes, **props}
    except:
        if logger:
            logger.debug(f"could not stat file {path=}", exc_info=True)
        return {}


def nbd_block_devices():
    logger = logging.getLogger(__name__)
    devices_and_partitions = {}

    util_parts = psutil.disk_partitions()
    mountpoint_map = {d.mountpoint: d.device for d in util_parts}
    device_map = {d.device: d.mountpoint for d in util_parts}
    mountpoint_util_parts_map = {util_parts[i].mountpoint: i
                                 for i in range(len(util_parts))}
    device_util_parts_map = {util_parts[i].device: i
                             for i in range(len(util_parts))}
    logger.debug(f"{util_parts=}")
    logger.debug(f"{mountpoint_map=}")
    logger.debug(f"{device_map=}")
    logger.debug(f"{mountpoint_util_parts_map=}")
    logger.debug(f"{device_util_parts_map=}")
    Disk = collections.namedtuple("Disk", [
        "name", "partitions", "mountpoints"]
        )
    for blockdev_stat in glob.glob('/sys/block/*/stat'):
        blockdev_dir = blockdev_stat.rsplit('/', 1)[0]
        name = blockdev_dir.rsplit('/', 1)[-1]
        if not name.startswith('nbd'):
            continue
        partitions = []
        mountpoints = []
        for part_stat in glob.glob(blockdev_dir + '/*/stat'):
            p_name = part_stat.rsplit('/', 2)[-2]
            partitions.append(p_name)
            devpath = f"/dev/{p_name}"
            if devpath in device_util_parts_map:
                i = device_util_parts_map[devpath]
                mountpoints.append(util_parts[i].mountpoint)
        d = Disk(name, partitions, mountpoints)
        devices_and_partitions[name] = d
    return devices_and_partitions


def get_unused_nbd_device():
    devices = nbd_block_devices()
    nbd_dev = None
    for d, i in devices.items():
        nbd_dev = d
        if len(i.mountpoints) == 0:
            break
    return nbd_dev


def get_current_nbd_disk(blk_info, mountpoint):
    for blockdev in blk_info['blockdevices']:
        if 'children' not in blockdev:
            continue
        for c in blockdev['children']:
            if mountpoint in c['mountpoints']:
                return blockdev['name']
    return None


def get_current_nbd_mountpoints(blk_info, mountpoint):
    blk = get_current_nbd_disk(blk_info, mountpoint)
    mnt = []
    for blockdev in blk_info['blockdevices']:
        if blockdev['name'] != blk:
            continue
        for c in blockdev['children']:
            for m in c['mountpoints']:
                if m and m.startswith(mountpoint):
                    mnt.append(m)
    return mnt


def interpolate_string(s, MINICLUSTER):
    return s.format(**MINICLUSTER._asdict())
