![](./.github/banner.png)

<p align="center">
  A python tool to generate an Excel file linking the list of cracked accounts and their LDAP attributes.  
  <br>
  <img alt="GitHub release (latest by date)" src="https://img.shields.io/github/v/release/p0dalirius/CrackedNTDStoXLSX">
  <a href="https://twitter.com/intent/follow?screen_name=podalirius_" title="Follow"><img src="https://img.shields.io/twitter/follow/podalirius_?label=Podalirius&style=social"></a>
  <a href="https://www.youtube.com/c/Podalirius_?sub_confirmation=1" title="Subscribe"><img alt="YouTube Channel Subscribers" src="https://img.shields.io/youtube/channel/subscribers/UCF_x5O7CSfr82AfNVTKOv_A?style=social"></a>
  <br>
</p>

## Features

 - [x] Authentications:
   - [x] Authenticate with password
   - [x] Authenticate with LM:NT hashes (Pass the Hash)
   - [x] Authenticate with kerberos ticket (Pass the Ticket)
 - [x] Exportable to XLSX format with option `--xlsx`

## Demonstration

This tool takes the output of hashcat 

```bash
./hashcat -m 1000 ./lab.local.ntds ./wordlists/rockyou.txt --username --show > cracked_ntds.txt
```

Then you can do:

```bash
./CrackedNTDStoXLSX.py -d 'LAB.local' -u 'user' -p 'P@ssw0rd' --dc-ip 10.0.0.101 -n cracked_ntds.txt -x cracked_users.xlsx
```

## Usage

```
$ ./CrackedNTDStoXLSX.py 
usage: CrackedNTDStoXLSX.py [-h] [--use-ldaps] [-debug] [-a ATTRIBUTES] -x XLSX -n NTDS [--dc-ip ip address] [--kdcHost FQDN KDC] [-d DOMAIN] [-u USER]
                            [--no-pass | -p PASSWORD | -H [LMHASH:]NTHASH | --aes-key hex key] [-k]

A python tool to generate an Excel file linking the list of cracked accounts and their LDAP attributes.

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

## Contributing

Pull requests are welcome. Feel free to open an issue if you want to add other features.