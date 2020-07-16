import logging
import colorama
from colorama import Fore, Style
from terminaltables import SingleTable
from pprint import pformat
import datetime
import re

from me4storage.api.session import Session
from me4storage.common.exceptions import ApiError
from me4storage.common.nsca import CheckResult
import me4storage.common.util as util
import me4storage.common.tables as tables
import me4storage.common.formatters

from me4storage.api import show, modify, create
from me4storage import commands

logger = logging.getLogger(__name__)

def disk_layout_me4084_linear_raid6(args, session):
    """ Fully configure empty ME4084 into typical disk configuration for Lustre OSTs

    This is a high-level function to fully configure an un-configured ME4084
    into a typical configuration for use as Lustre OSTs. This configuration
    involves creating 8x Linear 10-disk RAID6 disk-groups

    """

    systems = show.system(session)
    system_name = systems[0].system_name

    disk_groups = show.disk_groups(session)
    if len(disk_groups) > 0:
        logger.warn(f"There are {len(disk_groups)} disk-groups already present. No action taken...")
        rc = CheckResult.WARNING
        return rc.value

    # Many assumptions baked in here.
    #
    # We expect 84 disks present, of which 80 are HDDs to be used to create
    # linear disk groups. The other 4 are either global-spare drives, or are
    # unused SSDs.
    #
    # We expect the first two slots of each drawer to be the 4 spare drives
    # so usable disks for configuration are:
    # 0.2-0.41 and 0.44-0.83 (where drawers range: 0.0-0.41 and 0.42-0.83)
    #
    # There is no way to make these raid-groups tolerate a draw failure,
    # like with the MD platform, thus we worry less about the exact layout
    # of the disks within the drawers
    #
    # We use a simple layout where we simply select disks in steps of '8'

    drawer_0_start_id = 2
    drawer_0_end_id = 42
    drawer_1_start_id = 44
    drawer_1_end_id = 84

    for i in range(0,8):
        start_id = drawer_0_start_id + i
        drawer_0_disks=list(range(start_id, drawer_0_end_id, 8))

        start_id = drawer_1_start_id + i
        drawer_1_disks=list(range(start_id, drawer_1_end_id, 8))

        disks = drawer_0_disks + drawer_1_disks

        enclosure_id = 0
        disk_ids = [ f"{enclosure_id}.{disk}" for disk in disks ]

        dg_index = i + 1
        dg_name = f"dg{dg_index}-{system_name}"


        logger.info(f"""Creating disk group: {dg_name}, """
                    f"""Disks: {",".join(disk_ids)}""")
        create.linear_disk_group(session,
                                 name=dg_name,
                                 disks=",".join(disk_ids),
                                 chunk_size="128",
                                 raid_level="raid6")

    disk_groups = show.disk_groups(session)
    for dg in disk_groups:
        volume_name = re.sub(r'^dg([0-9]+\-.*)',r'v\1',dg.name)
        volume_size = dg.size
        logger.info(f"""Creating volume: {volume_name}, of size """
                    f"""{volume_size} on disk group: {dg.name}""")
        create.linear_volume(session,
                             name=volume_name,
                             disk_group=dg.name,
                             size=volume_size)

    rc = CheckResult.OK
    return rc.value
