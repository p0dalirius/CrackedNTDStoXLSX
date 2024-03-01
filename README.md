# CrackedNTDStoXLSX

## Usage

```
$ ./CrackedNTDStoXLSX.py 
usage: CrackedNTDStoXLSX.py [-h] [--use-ldaps] [-debug] [-a ATTRIBUTES] -x XLSX -n NTDS [--dc-ip ip address] [--kdcHost FQDN KDC] [-d DOMAIN] [-u USER]
                            [--no-pass | -p PASSWORD | -H [LMHASH:]NTHASH | --aes-key hex key] [-k]

CrackedNTDStoXLSX.py

options:
  -h, --help            show this help message and exit
  --use-ldaps           Use LDAPS instead of LDAP
  -debug                Debug mode
  -a ATTRIBUTES, --attribute ATTRIBUTES
                        Attributes to extract.
  -x XLSX, --xlsx XLSX  Output results to an XLSX file.
  -n NTDS, --ntds NTDS  Output results to an XLSX file.

authentication & connection:
  --dc-ip ip address    IP Address of the domain controller or KDC (Key Distribution Center) for Kerberos. If omitted it will use the domain part (FQDN) specified in the identity parameter
  --kdcHost FQDN KDC    FQDN of KDC for Kerberos.
  -d DOMAIN, --domain DOMAIN
                        (FQDN) domain to authenticate to
  -u USER, --user USER  user to authenticate with

  --no-pass             don't ask for password (useful for -k)
  -p PASSWORD, --password PASSWORD
                        password to authenticate with
  -H [LMHASH:]NTHASH, --hashes [LMHASH:]NTHASH
                        NT/LM hashes, format is LMhash:NThash
  --aes-key hex key     AES key to use for Kerberos Authentication (128 or 256 bits)
  -k, --kerberos        Use Kerberos authentication. Grabs credentials from .ccache file (KRB5CCNAME) based on target parameters. If valid credentials cannot be found, it will use the ones specified in the
                        command line
```
