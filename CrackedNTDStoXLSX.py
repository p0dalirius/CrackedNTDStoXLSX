#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : CrackedNTDStoXLSX.py
# Author             : Podalirius (@podalirius_)
# Date created       : 01 March 2023


import argparse
from ldap3.protocol.formatters.formatters import format_sid
import ldap3
from sectools.windows.ldap import init_ldap_session
import os
import traceback
import sys
import xlsxwriter
from rich.progress import track


VERSION = "1.1"


# LDAP controls
# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/3c5e87db-4728-4f29-b164-01dd7d7391ea
LDAP_PAGED_RESULT_OID_STRING = "1.2.840.113556.1.4.319"
# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/f14f3610-ee22-4d07-8a24-1bf1466cba5f
LDAP_SERVER_NOTIFICATION_OID = "1.2.840.113556.1.4.528"

class LDAPSearcher(object):
    def __init__(self, ldap_server, ldap_session):
        super(LDAPSearcher, self).__init__()
        self.ldap_server = ldap_server
        self.ldap_session = ldap_session

    def query(self, base_dn, query, attributes=['*'], page_size=1000):
        """
        Executes an LDAP query with optional notification control.

        This method performs an LDAP search operation based on the provided query and attributes. It supports
        pagination to handle large datasets and can optionally enable notification control to receive updates
        about changes in the LDAP directory.

        Parameters:
        - query (str): The LDAP query string.
        - attributes (list of str): A list of attribute names to include in the search results. Defaults to ['*'], which returns all attributes.
        - notify (bool): If True, enables the LDAP server notification control to receive updates about changes. Defaults to False.

        Returns:
        - dict: A dictionary where each key is a distinguished name (DN) and each value is a dictionary of attributes for that DN.

        Raises:
        - ldap3.core.exceptions.LDAPInvalidFilterError: If the provided query string is not a valid LDAP filter.
        - Exception: For any other issues encountered during the search operation.
        """

        results = {}
        try:
            # https://ldap3.readthedocs.io/en/latest/searches.html#the-search-operation
            paged_response = True
            paged_cookie = None
            while paged_response == True:
                self.ldap_session.search(
                    base_dn,
                    query,
                    attributes=attributes,
                    size_limit=0,
                    paged_size=page_size,
                    paged_cookie=paged_cookie
                )
                if "controls" in self.ldap_session.result.keys():
                    if LDAP_PAGED_RESULT_OID_STRING in self.ldap_session.result["controls"].keys():
                        next_cookie = self.ldap_session.result["controls"][LDAP_PAGED_RESULT_OID_STRING]["value"]["cookie"]
                        if len(next_cookie) == 0:
                            paged_response = False
                        else:
                            paged_response = True
                            paged_cookie = next_cookie
                    else:
                        paged_response = False
                else:
                    paged_response = False
                for entry in self.ldap_session.response:
                    if entry['type'] != 'searchResEntry':
                        continue
                    results[entry['dn']] = entry["attributes"]
        except ldap3.core.exceptions.LDAPInvalidFilterError as e:
            print("Invalid Filter. (ldap3.core.exceptions.LDAPInvalidFilterError)")
        except Exception as e:
            raise e
        return results

    def query_all_naming_contexts(self, query, attributes=['*'], page_size=1000):
        """
        Queries all naming contexts on the LDAP server with the given query and attributes.

        This method iterates over all naming contexts retrieved from the LDAP server's information,
        performing a paged search for each context using the provided query and attributes. The results
        are aggregated and returned as a dictionary where each key is a distinguished name (DN) and
        each value is a dictionary of attributes for that DN.

        Parameters:
        - query (str): The LDAP query to execute.
        - attributes (list of str): A list of attribute names to retrieve for each entry. Defaults to ['*'] which fetches all attributes.

        Returns:
        - dict: A dictionary where each key is a DN and each value is a dictionary of attributes for that DN.
        """

        results = {}
        try:
            for naming_context in self.ldap_server.info.naming_contexts:
                paged_response = True
                paged_cookie = None
                while paged_response == True:
                    self.ldap_session.search(
                        naming_context,
                        query,
                        attributes=attributes,
                        size_limit=0,
                        paged_size=self.page_size,
                        paged_cookie=paged_cookie
                    )
                    if "controls" in self.ldap_session.result.keys():
                        if LDAP_PAGED_RESULT_OID_STRING in self.ldap_session.result["controls"].keys():
                            next_cookie = self.ldap_session.result["controls"][LDAP_PAGED_RESULT_OID_STRING]["value"]["cookie"]
                            if len(next_cookie) == 0:
                                paged_response = False
                            else:
                                paged_response = True
                                paged_cookie = next_cookie
                        else:
                            paged_response = False
                    else:
                        paged_response = False
                    for entry in self.ldap_session.response:
                        if entry['type'] != 'searchResEntry':
                            continue
                        results[entry['dn']] = entry["attributes"]
        except ldap3.core.exceptions.LDAPInvalidFilterError as e:
            print("Invalid Filter. (ldap3.core.exceptions.LDAPInvalidFilterError)")
        except Exception as e:
            raise e
        return results


def parse_args():
    default_attributes = ["accountExpires", "company", "department", "description", "displayName", "distinguishedName", "lastLogon", "lastLogonTimestamp", "memberOf", "whenChanged", "whenCreated"]

    parser = argparse.ArgumentParser(add_help=True, description='A python tool to generate an Excel file linking the list of cracked accounts and their LDAP attributes.')
    parser.add_argument('--use-ldaps', action='store_true', help='Use LDAPS instead of LDAP')
    parser.add_argument("-debug", dest="debug", action="store_true", default=False, help="Debug mode")

    parser.add_argument("-a", "--attribute", dest="attributes", default=default_attributes, action="append", type=str, help="Attributes to extract.")
    
    parser.add_argument("-x", "--xlsx", dest="xlsx", default=None, type=str, required=True, help="Output results to an XLSX file.")
    parser.add_argument("-n", "--ntds", dest="ntds", default=None, type=str, required=True, help="Output results to an XLSX file.")

    authconn = parser.add_argument_group('authentication & connection')
    authconn.add_argument('--dc-ip', action='store', metavar="ip address", help='IP Address of the domain controller or KDC (Key Distribution Center) for Kerberos. If omitted it will use the domain part (FQDN) specified in the identity parameter')
    authconn.add_argument('--kdcHost', dest="kdcHost", action='store', metavar="FQDN KDC", help='FQDN of KDC for Kerberos.')
    authconn.add_argument("-d", "--domain", dest="auth_domain", metavar="DOMAIN", action="store", help="(FQDN) domain to authenticate to")
    authconn.add_argument("-u", "--user", dest="auth_username", metavar="USER", action="store", help="user to authenticate with")

    secret = parser.add_argument_group()
    cred = secret.add_mutually_exclusive_group()
    cred.add_argument('--no-pass', action="store_true", help='don\'t ask for password (useful for -k)')
    cred.add_argument("-p", "--password", dest="auth_password", metavar="PASSWORD", action="store", help="password to authenticate with")
    cred.add_argument("-H", "--hashes", dest="auth_hashes", action="store", metavar="[LMHASH:]NTHASH", help='NT/LM hashes, format is LMhash:NThash')
    cred.add_argument('--aes-key', dest="auth_key", action="store", metavar="hex key", help='AES key to use for Kerberos Authentication (128 or 256 bits)')
    secret.add_argument("-k", "--kerberos", dest="use_kerberos", action="store_true", help='Use Kerberos authentication. Grabs credentials from .ccache file (KRB5CCNAME) based on target parameters. If valid credentials cannot be found, it will use the ones specified in the command line')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    return args


def export_xlsx(options, results):
    # Prepare file path
    basepath = os.path.dirname(options.xlsx)
    filename = os.path.basename(options.xlsx)
    if basepath not in [".", ""]:
        if not os.path.exists(basepath):
            os.makedirs(basepath)
        path_to_file = basepath + os.path.sep + filename
    else:
        path_to_file = filename
    
    # Create Excel workbook
    # https://xlsxwriter.readthedocs.io/workbook.html#Workbook
    workbook_options = {
        'constant_memory': True, 
        'in_memory': True, 
        'strings_to_formulas': False,
        'remove_timezone': True
    }
    workbook = xlsxwriter.Workbook(filename=path_to_file, options=workbook_options)
    worksheet = workbook.add_worksheet()
    
    # Prepare attributes
    if '*' in options.attributes:
        attributes = []
        options.attributes.remove('*')
        attributes += options.attributes
        for entry, ldapresults in results:
            for dn in ldapresults.keys():
                attributes = sorted(list(set(attributes + list(ldapresults[dn].keys()))))
    else:
        attributes = options.attributes
   
    # Format colmun headers
    header_format = workbook.add_format({'bold': 1})
    header_format.set_pattern(1)
    header_format.set_bg_color('green')
    
    header_fields = ["domain", "username", "nthash", "password"]
    header_fields = header_fields + attributes
    for k in range(len(header_fields)):
        worksheet.set_column(k, k + 1, len(header_fields[k]) + 3)
    worksheet.set_row(row=0, height=40, cell_format=header_format)
    worksheet.write_row(row=0, col=0, data=header_fields)

    row_id = 1
    for entry, ldapresults in results:
        data = [entry["domain"], entry["username"], entry["nthash"], entry["password"]]
        if len(ldapresults.keys()) != 1:
            if len(ldapresults.keys()) == 0:
                worksheet.write_row(row=row_id, col=0, data=data)
            else:
                print("Error for entry:", entry)
                print(list(ldapresults.keys()))
        else:
            for dn in ldapresults.keys():
                for attr in attributes:
                    if attr in ldapresults[dn].keys():
                        value = ldapresults[dn][attr]
                        if type(value) == str:
                            data.append(value)
                        elif type(value) == bytes:
                            data.append(str(value))
                        elif type(value) == list:
                            data.append('\n'.join([str(l) for l in value]))
                        else:
                            data.append(str(value))
                    else:
                        data.append("")
                worksheet.write_row(row=row_id, col=0, data=data)
        row_id += 1

    worksheet.autofilter(
        first_row=0, 
        first_col=0, 
        last_row=row_id, 
        last_col=(len(header_fields)-1)
    )
    workbook.close()

    print("[>] Written '%s'" % path_to_file)

if __name__ == '__main__':
    options = parse_args()

    print("CrackedNTDStoXLSX.py v%s - by @podalirius_\n" % VERSION)

    # Parse hashes
    auth_lm_hash = ""
    auth_nt_hash = ""
    if options.auth_hashes is not None:
        if ":" in options.auth_hashes:
            auth_lm_hash = options.auth_hashes.split(":")[0]
            auth_nt_hash = options.auth_hashes.split(":")[1]
        else:
            auth_nt_hash = options.auth_hashes
    
    # Use AES Authentication key if available
    if options.auth_key is not None:
        options.use_kerberos = True
    if options.use_kerberos is True and options.kdcHost is None:
        print("[!] Specify KDC's Hostname of FQDN using the argument --kdcHost")
        exit()
    
    # Try to authenticate with specified credentials
    try:
        print("[>] Try to authenticate as '%s\\%s' on %s ... " % (options.auth_domain, options.auth_username, options.dc_ip))
        ldap_server, ldap_session = init_ldap_session(
            auth_domain=options.auth_domain,
            auth_dc_ip=options.dc_ip,
            auth_username=options.auth_username,
            auth_password=options.auth_password,
            auth_lm_hash=auth_lm_hash,
            auth_nt_hash=auth_nt_hash,
            auth_key=options.auth_key,
            use_kerberos=options.use_kerberos,
            kdcHost=options.kdcHost,
            use_ldaps=options.use_ldaps
        )
        print("[+] Authentication successful!\n")

        search_base = ldap_server.info.other["defaultNamingContext"][0]
        ls = LDAPSearcher(ldap_server=ldap_server, ldap_session=ldap_session)

        f = open(options.ntds, "r")
        entries = []
        for line in f.readlines():
            cracked_identity, cracked_nthash, cracked_password = line.strip('\n').split(':',2)
            if '\\' in cracked_identity:
                cracked_domain = cracked_identity.split('\\',1)[0]
                cracked_username = cracked_identity.split('\\',1)[1]
            else:
                cracked_domain = ""
                cracked_username = cracked_identity
            entries.append({
                "domain": cracked_domain,
                "username": cracked_username,
                "nthash": cracked_nthash,
                "password": cracked_password
            })
        f.close()

        results = []
        for entry in track(entries, description="Matching cracked users with the LDAP ..."):
            ldap_query = '(sAMAccountName=%s)' % entry["username"]
            ldap_results = ls.query(base_dn=search_base, query=ldap_query, attributes=options.attributes)
            results.append((entry, ldap_results))

        export_xlsx(options, results)

    except Exception as e:
        if options.debug:
            traceback.print_exc()
        print("[!] Error: %s" % str(e))
