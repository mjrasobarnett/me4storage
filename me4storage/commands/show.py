import logging
import colorama
from colorama import Fore, Style
from terminaltables import SingleTable
from pprint import pformat
import datetime

from me4storage.api.session import Session
from me4storage.common.exceptions import ApiError
from me4storage.common.nsca import CheckResult
import me4storage.common.util as util
import me4storage.common.tables as tables
import me4storage.common.formatters

from me4storage.api import show

logger = logging.getLogger(__name__)

def system_info(args, session):

    systems = show.system(session)
    service_tags = show.service_tag_info(session)
    ntp_instances = show.ntp_status(session)

    rc = CheckResult.OK
    for system in systems:
        print(f"{Fore.WHITE}{Style.BRIGHT}System: {system.system_name}{Style.RESET_ALL}")
        print(f"  Product Type:    {system.product_id}")
        print(f"  Contact:         {system.system_contact}")
        print(f"  Description:     {system.system_information}")
        print(f"  Location:        {system.system_location}")

    print(f"\nService Tags:")
    for service_tag in service_tags:
        print(f"  Enclosure {service_tag.enclosure_id}:     {service_tag.service_tag}")

    return rc.value



def network(args, session):

    systems = show.system(session)
    ntp_instances = show.ntp_status(session)
    dns_instances = show.dns(session)
    hostnames = show.dns_management_hostname(session)

    rc = CheckResult.OK
    for system in systems:
        print(f"{Fore.WHITE}{Style.BRIGHT}System: {system.system_name}{Style.RESET_ALL}")

        print(f"\nNTP:")
        for ntp in ntp_instances:
            print(f"  Status:          {ntp.ntp_status}")
            print(f"  Server:          {ntp.ntp_server_address}")
            print(f"  Time (UTC):      {ntp.ntp_contact_time}")

        print(f"\nDNS:")
        for dns in dns_instances:
            print(f"  Controller:        {dns.controller_numeric}")
            for mgmt in hostnames:
                if dns.controller_numeric == mgmt.controller_numeric:
                    print(f"    Mgmt Hostname:   {mgmt.mgmt_hostname}")
            print(f"    Server(s):       {dns.name_servers}")
            print(f"    Search Domains:  {dns.search_domains}")

    return rc.value



