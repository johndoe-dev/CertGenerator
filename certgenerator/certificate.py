import csv
import logging
import logging.handlers
import os
import json
import click
import shutil
from glob import glob
from OpenSSL import crypto
from tools import Tools, yaml
from cert_exceptions import *


class Certificate:

    def __init__(self, logger=None, opts={}):
        """
        Init class with logger and opts
        :param logger:
        :param opts:
        """
        self._verbose = False
        self._debug = False
        self._logger = logger
        self.allowed = ["Digital Signature", "Non Repudiation", "Key Encipherment"]
        self.ctx = None

        # Set directories path
        self.tools = Tools()
        self.tools.load_config()
        self.basedir = self.tools.here
        self.Documents = self.tools.documents
        self.config_folder = self.get_folder(os.path.join(self.basedir, "config"))
        self.app_folder = self.get_folder(self.tools.app_folder)
        self.certificate_folder = self.get_folder(os.path.join(self.app_folder, "certificate"))
        self.csv_folder = self.get_folder(os.path.join(self.app_folder, "csv"))
        self.csr_folder = self.get_folder(os.path.join(self.certificate_folder, "csr"))
        self.p12_folder = self.get_folder(os.path.join(self.certificate_folder, "p12"))

        # Set default usage
        self.TYPE_RSA = crypto.TYPE_RSA
        self.name = None
        self.key_file = None
        self.csr_file = None
        self.p12_file = None
        self._level = logging.WARNING
        self._key_size = 2048
        self._ca = False
        self.usage = ','.join(self.allowed)
        self.config = None
        self.subject = {}

        # Set click ctx
        try:
            self.ctx = opts['ctx']
            del opts['ctx']
        except KeyError:
            pass

        # Set verbose
        try:
            self._verbose = opts['verbose']
            del opts['verbose']
        except KeyError:
            pass

        # Set debug
        try:
            self._debug = opts['debug']
            del opts['debug']
        except KeyError:
            pass

        # Set default log level
        try:
            self._level = opts['level']
            del opts['level']
        except KeyError:
            pass

        # Set Key size
        try:
            if opts.get('size') and int(opts.get('size')) in [1024, 2048, 4096]:
                self._key_size = int(opts.get('size'))
            del opts['size']
        except KeyError:
            pass
        except ValueError:
            pass

        # Set config
        try:
            self.config = opts.get('config')
            del opts['config']
        except KeyError:
            pass

        try:
            self.custom = opts.get('custom')
            del opts['custom']
        except KeyError:
            pass

        self.copy_config_files()

        self.opts = opts
        self.output('[*] We have already set options:', level=logging.DEBUG)
        self.output('{o}'.format(o=self.opts), level=logging.DEBUG)

        if self.config and "yamlfile" in self.config:
            self.load_subject(self.config.get("yamlfile"))

    def copy_config_files(self):
        """
        Copy csv files and yaml file in app_folder if doesn't exist
        :return:
        """
        # copy all csv file from config to csv folder
        for _csv_path in glob(os.path.join(self.config_folder, "*.csv")):
            _csv = _csv_path.split("/")[-1]
            if not os.path.exists(os.path.join(self.csv_folder, _csv)):
                shutil.copy2(_csv_path, self.csv_folder)

        # copy yaml file from config to app folder
        for _yaml_path in glob(os.path.join(self.config_folder, "*.yaml")):
            _yaml = _yaml_path.split('/')[-1]
            if not os.path.exists(os.path.join(self.app_folder, _yaml)):
                shutil.copy2(_yaml_path, self.app_folder)

    def generate_key(self):
        """
        Generate private key
        :return: key
        """
        key = crypto.PKey()
        key.generate_key(self.TYPE_RSA, self._key_size)

        return key

    def generate_csr(self, force=False):
        """
        Generate csr file
        :param force
        :return:
        """
        self.get_csr_name()

        san = self.get_san()

        req = crypto.X509Req()
        self.fill_subject(req)

        base_constraints = ([
            crypto.X509Extension("keyUsage", False, self.usage),
            crypto.X509Extension("basicConstraints", False, "CA:{c}".format(c=self.is_ca())),
        ])
        x509_extensions = base_constraints

        if san:
            san_constraint = crypto.X509Extension("subjectAltName", False, san)
            x509_extensions.append(san_constraint)

        req.add_extensions(x509_extensions)

        key = self.generate_key()
        req.set_pubkey(key)
        req.sign(key, "sha256")

        self.output("=========== generate {} ============".format(self.name), level=logging.DEBUG)
        if force:
            self.overwrite_csr(req=req, key=key)
        else:
            self.write_csr(req=req, key=key)

    def generate_multiple(self, csv_file=None, force=False):
        """
        Generate .csr for each serial
        :param csv_file:
        :param force
        :return:
        """

        absolute = self.is_absolute(csv_file)

        _list = self.get_list_from_csv(csv_file=csv_file, absolute=absolute)

        for name in _list:
            self.create_request(name=name)
            self.set_subject(CN=name)
            self.generate_csr(force=force)

    def generate_p12(self, key=None, pem=None, p12=None, password="3z6F2Xfc", force=False):
        """
        Generate p12 file
        :param key:
        :param pem:
        :param p12:
        :param password:
        :param force:
        :return:
        """
        self.output("=========== generate {} ============".format(p12), level=logging.DEBUG)
        generated = True
        if self.check_extension(p12, "p12"):
            if not self.exists(self.p12_folder):
                self.output("Create p12 folder", level=logging.DEBUG)
                os.mkdir(self.p12_folder)
            if force:
                generated = self.overwrite_p12(p12=p12, key=key, pem=pem, password=password)
            else:
                generated = self.write_p12(p12=p12, key=key, pem=pem, password=password)
        try:
            os.remove(p12)
        except OSError:
            pass
        if generated:
            self.output("=========== {} generated ============".format(p12), level=logging.DEBUG)
        else:
            self.output("=========== {} not generated ============".format(p12), level=logging.DEBUG)

    def generate_multiple_p12(self, pem_folder, key_folder=None, csv_file=None, force=False):
        """
        Generate multiple p12 file
        :param pem_folder:
        :param key_folder:
        :param csv_file:
        :param force:
        :return:
        """

        absolute = self.is_absolute(csv_file)

        _list = self.get_list_from_csv(csv_file=csv_file, absolute=absolute)

        certificate = self.csr_folder

        if key_folder:
            if self.exists(key_folder, trigger_error=True):
                pass

        if not pem_folder:
            self.output("pem folder must be defined", level=logging.ERROR)

        if self.exists(pem_folder, trigger_error=True):
            for name in _list:
                if key_folder:
                    key = os.path.join(key_folder, name + ".key")
                else:
                    key = os.path.join(certificate, name, name + ".key")
                pem = os.path.join(pem_folder, name + ".pem")
                p12 = name + ".p12"
                if self.exists(key) and self.exists(pem):
                    self.generate_p12(key=key, pem=pem, p12=p12, force=force)

    def get_csr_name(self):
        """
        Check csr_file
        :return:
        """
        if self.csr_file is None:
            name = None
            if "name" in self.opts:
                name = self.opts['name']
            else:
                if "CN" in self.subject:
                    name = self.subject['CN']
                if self.config and "csr_name" in self.config:
                    name = self.config.get("csr_name")
            if name is None:
                self.output("Could not generate certificate with empty name", level=logging.ERROR)
            self.set_subject(CN=name)
            self.create_request(name=name)

    def get_san(self):
        """
        check if san is given
        :return:
        """
        cfg = {}
        ss = []
        if self.config and "yamlfile" in self.config:
            cfg = self.parse_yaml(self.config.get("yamlfile"))

        if "san" in cfg:
            for entry in cfg["san"].split(" "):
                ss.append("DNS: {e}".format(e=entry))
        else:
            try:
                for entry in self.opts["san"]:
                    ss.append("DNS: {e}".format(e=entry))
            except KeyError:
                pass

        if ss:
            ss = ", ".join(ss)
            self.output("Subject Alt Name (san): {san} added".format(san=ss), level=logging.DEBUG)

        if len(ss):
            return ss
        return None

    def create_request(self, name):
        """
        create empty csr and key files
        :param name:
        :return:
        """
        self.name = name
        r_folder = os.path.join(self.csr_folder, name)
        if not self.exists(r_folder):
            os.mkdir(r_folder)
            self.output("{} folder created".format(r_folder), level=logging.DEBUG)
        self.csr_file = os.path.join(r_folder, name + ".csr")
        self.key_file = os.path.join(r_folder, name + ".key")

    def get_folder(self, path):
        """
        Return certificate folder
        :param path:
        :return:
        """
        if not self.exists(path):
            os.mkdir(path)
        return path

    def load_subject(self, cfg=None):
        """
        Define subject from yaml file or opts['subject']
        :param cfg:
        :return:
        """
        _cfg = None
        if cfg:
            try:
                _cfg = self.parse_yaml(cfg)
            except Exception as err:
                self.output(err, level=logging.ERROR)
        else:
            _cfg = self.opts["subject"]

        self.output("=========== configure Subject ============", level=logging.DEBUG)
        self.set_subject(_dict=_cfg)
        self.output("=========== end configuring Subject ============", level=logging.DEBUG)

    def fill_subject(self, cert, self_signed=False):
        """
        add subject to cert
        :param cert:
        :param self_signed:
        :return:
        """
        if "C" in self.subject:
            cert.get_subject().countryName = self.subject.get("C")
        if "ST" in self.subject:
            cert.get_subject().stateOrProvinceName = self.subject.get("ST")
        if "L" in self.subject:
            cert.get_subject().localityName = self.subject.get("L")
        if "O" in self.subject:
            cert.get_subject().organizationName = self.subject.get("O")
        if "OU" in self.subject:
            cert.get_subject().organizationalUnitName = self.subject.get("OU")
        if "CN" in self.subject:
            cert.get_subject().CN = self.subject.get("CN")
        if "emailAddress" in self.subject:
            cert.get_subject().emailAddress = self.subject.get('emailAddress')
        if self_signed:
            cert.set_issuer(cert.get_subject())

    def set_subject(self, _dict={}, **kwargs):
        """
        add or update subject
        :param _dict
        :param kwargs:
        :return:
        """
        _dict.update(kwargs)

        fields = ["C", "CN", "ST", "L", "O", "OU", "emailAddress"]

        for k, v in _dict.items():
            if k in fields:
                if (k == "C") and len(v) != 2:
                    continue
                if len(v) == 0:
                    continue
                if (k == "CN") and self.subject.get(k) and len(self.subject[k]) > 0:
                    continue
                self.subject.update({k: v})
                self.output("subject => {k} : {v} added".format(k=k, v=self.subject[k]), level=logging.DEBUG)

    def get_subject(self, key=None):
        """
        Return subject
        :param key: if key, return subect[key]
        :return:
        """
        if key:
            if self.subject.get(key):
                return self.subject.get(key)
            return None
        return self.subject

    def overwrite_p12(self, p12, key, pem, password):
        """
        :param p12:
        :param key:
        :param pem:
        :param password:
        :return:
        """
        if self.exists(key, trigger_error=True) and self.exists(pem, trigger_error=True):
            if self.check_extension(key, "key") and self.check_extension(pem, "pem"):
                cmd = "openssl pkcs12 -inkey {key} -in {pem} -export -out {p12} -password pass:{p}" \
                    .format(key=key, pem=pem, p12=p12, p=password)
                self.shell(cmd)
                if self.exists(p12) and self.check_p12(path=p12, password=password, read=False):
                    self.output("move {p} to {f}".format(p=p12, f=self.p12_folder), level=logging.DEBUG)
                    os.rename(p12, os.path.join(self.p12_folder, p12))
                    click.echo("{n} generated in {p}\n".format(n=p12, p=self.p12_folder))
        return True

    def write_p12(self, p12, key, pem, password):
        """
        :param p12:
        :param key:
        :param pem:
        :param password:
        :return:
        """
        if self.exists(os.path.join(self.p12_folder, p12), trigger_warning=False):
            self.output("{f} already exists, abort".format(f=p12))
            return False
        else:
            if self.exists(key, trigger_error=True) and self.exists(pem, trigger_error=True):
                if self.check_extension(key, "key") and self.check_extension(pem, "pem"):
                    cmd = "openssl pkcs12 -inkey {key} -in {pem} -export -out {p12} -password pass:{p}" \
                        .format(key=key, pem=pem, p12=p12, p=password)
                    self.shell(cmd)
                    if self.exists(p12) and self.check_p12(path=p12, password=password, read=False):
                        self.output("move {p} to {f}".format(p=p12, f=self.p12_folder), level=logging.DEBUG)
                        os.rename(p12, os.path.join(self.p12_folder, p12))
                        click.echo("{n} generated in {p}\n".format(n=p12, p=self.p12_folder))
        return True

    def overwrite_csr(self, req, key):
        """
        Overwrite csr file
        :param req:
        :param key:
        :return:
        """
        self.generate_file(self.key_file, key)
        self.generate_file(self.csr_file, req)
        self.output("=========== {} generated ============".format(self.name), level=logging.DEBUG)
        click.echo("{n} generated in {p}\n".format(n=self.name, p=self.csr_folder))

    def write_csr(self, req, key):
        """
        Write csr file
        :param req:
        :param key:
        :return:
        """
        if self.exists(self.csr_file) and self.exists(self.key_file):
            self.output("{} already exists => abort".format(self.name))
        else:
            self.generate_file(self.key_file, key)
            self.generate_file(self.csr_file, req)
            self.output("=========== {} generated ============".format(self.name), level=logging.DEBUG)
            click.echo("{n} generated in {p}\n".format(n=self.name, p=self.csr_folder))

    def generate_file(self, mk_file, request):
        """
        Generate .csr/key files.
        :param mk_file:
        :param request:
        :return:
        """
        with open(mk_file, "w") as f:
            if ".csr" in mk_file:
                f.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, request))
                self.output("csr : {} generated".format(mk_file), level=logging.DEBUG)
            elif ".key" in mk_file:
                f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, request))
                self.output("private key : {} generated".format(mk_file), level=logging.DEBUG)
            elif ".crt" in mk_file:
                f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, request))

    def is_ca(self):
        """
        Return TRUE or FALSE on string format
        :return:
        """
        return "TRUE" if self._ca else "FALSE"

    def output(self, msg, level=logging.WARNING):
        """
        Generate output to CLI and log file
        :param msg:
        :param level:
        :return:
        """

        # Output to log
        if level == logging.DEBUG:
            self._logger.debug(msg)
        elif level == logging.INFO:
            self._logger.info(msg)
        elif level == logging.WARNING:
            self._logger.warning(msg)
        elif level == logging.ERROR:
            self._logger.error(msg)
            click.echo(self.ctx.get_help() + "\n")
            click.echo("\n========ERROR========\n{m}\n========ERROR========\n".format(m=msg))
            raise click.Abort()
        elif level == logging.CRITICAL:
            self._logger.critical(msg)
        # Misconfigured level are high notifications
        else:
            self._logger.error("[!] Invalid level for message: {m}".format(m=msg))

        # Output to CLI if needed
        if self._verbose and (level >= self._level):
            click.echo("{m}\n".format(m=msg))

        elif self._debug:
            click.echo("{m}\n".format(m=msg))

    def read(self, path, password=None, plain_text=False):
        """
        Read file in terminal read csr and p12
        :param path:
        :param password: Use only to read p12 file
        :param plain_text:
        :return:
        """
        if self.exists(path, trigger_error=True):
            self.output("============== Read Certificate =================", level=logging.DEBUG)
            if self.check_extension(path, "csr", trigger_error=False):
                return self.check_csr(path, plain_text=plain_text)
            elif self.check_extension(path, "p12", trigger_error=False):
                return self.check_p12(path=path, password=password)
            else:
                self.output(".csr or .p12 expected", logging.ERROR)

    def check_csr(self, path, read=True, plain_text=False):
        """
        Check csr
        :param path:
        :param read:
        :param plain_text:
        :return:
        """

        if not plain_text:
            try:

                with open(path) as f:
                    _file = f.read()
                self.output("Read {f}".format(f=path), level=logging.DEBUG)
                req = crypto.load_certificate_request(crypto.FILETYPE_PEM, _file)
                key = req.get_pubkey()
                extensions = self.get_cert_ext(req)
                key_type = 'RSA' if key.type() == crypto.TYPE_RSA else 'DSA'
                self.output("get subject", level=logging.DEBUG)
                subject = req.get_subject()
                components = dict(subject.get_components())
                result = {
                    "Common name:": components['CN'] if "CN" in components else "",
                    "Organisation:": components['O'] if "O" in components else "",
                    "Orgainistional unit": components['OU'] if "OU" in components else "",
                    "City/locality:": components['L'] if 'L' in components else "",
                    "State/province:": components['ST'] if "ST" in components else "",
                    "Country:": components['C'] if "C" in components else "",
                    "Signature algorithm:": '',
                    "Key algorithm:": key_type,
                    "Key size:": key.bits(),
                    "extensions:": extensions
                }
                if read:
                    self.output("Generate json", level=logging.DEBUG)
                    return json.dumps(result, indent=4)
                return True
            except Exception as e:
                m = "Failed to read {f}\n {e}\nTry read {f} -t".format(f=path, e=e)
                if read:
                    self.output(m, level=logging.ERROR)
                else:
                    self.output(m, level=logging.WARNING)
                    return False
        else:
            cmd = "openssl req -text -noout -text -in {}".format(path)
            result = self.shell(cmd)
            if result:
                return result
            else:
                self.output("unable to read {f}".format(f=path), level=logging.ERROR)

    def check_p12(self, path, password=None, read=True):
        """
        check p12
        :param path:
        :param password:
        :param read:
        :return:
        """
        # if password:
        #     cmd = "openssl pkcs12 -info -in {p12} -noout -password pass:{p}".format(p12=path, p=password)
        # else:
        #     cmd = "openssl pkcs12 -info -in {p12}".format(p12=path)
        # result = self.shell(cmd)
        # if result:
        #     return result
        # else:
        #     return False

        try:
            if not password:
                password = str(click.prompt("Enter password"))
            self.output("Read {f}".format(f=path), level=logging.DEBUG)
            p12 = crypto.load_pkcs12(open(path, 'rb').read(), password)

            s = str(p12.get_certificate().get_subject()).split("<X509Name object ")[1].split(">")[0].split("/")
            subject = {}
            for i in s:
                try:
                    subject[i.split("=")[0]] = i.split("=")[1]
                except IndexError:
                    pass

            result = {
                "certificate:": {
                    "subject": subject
                },
                "private_key:": {
                    "type": str(p12.get_privatekey().type()),
                    "bits": str(p12.get_privatekey().bits())
                },
                "ca:": str(p12.get_ca_certificates())
            }
            if read:
                self.output("Generate json", level=logging.DEBUG)
                return json.dumps(result, indent=4)
            return True
        except Exception as e:
            if read:
                self.output("Failed to read {f}\n {e}".format(f=path, e=e), level=logging.ERROR)
            else:
                self.output("Failed to read {f}\n {e}".format(f=path, e=e), level=logging.WARNING)
                return False

    @staticmethod
    def get_cert_ext(req):
        """
        Return extension from X509Object
        :param req:
        :return:
        """
        ext = []
        for i in req.get_extensions():
            ext.append(str(i))
        return ext

    def get_list_from_csv(self, csv_file=None, absolute=False):
        _list = []
        if csv_file:
            _list = self.read_csv(_file=csv_file, absolute=absolute)
        elif self.custom and "csvfile" in self.custom:
            _list = self.read_csv(_file=self.custom.get("csvfile"))
        elif self.config and "csvfile" in self.config:
            _list = self.read_csv(_file=self.config.get("csvfile"))
        if not _list:
            self.output("no csv file or list detected", level=logging.ERROR)
        return _list

    def read_csv(self, _file, absolute=False):
        """
        Return dict form csv file
        :param _file:
        :param absolute:
        :return:
        """
        csv_file = os.path.join(self.csv_folder, _file)
        if absolute:
            csv_file = _file
        csv_list = []
        column = "serial"
        try:
            if self.check_extension(csv_file, "csv"):
                self.output("[+] Reading values file: {f}".format(f=_file), level=logging.DEBUG)
                with open(csv_file) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        csv_list.append(row[column])
                return csv_list
        except IOError as err:
            self.output(err, level=logging.ERROR)
        except KeyError:
            self.output("You must name your head column: '{c}' in the csv file: {f}".format(c=column, f=csv_file),
                        level=logging.ERROR)

    def exists(self, path, trigger_error=False, trigger_warning=True):
        """
        Check if pat exist
        :param path:
        :param trigger_error: display error and stop program if True
        :param trigger_warning: display warning if True
        :return:
        """
        try:
            if os.path.exists(path):
                return True
            if trigger_error:
                self.output("{f} doesn't exist".format(f=path), level=logging.ERROR)
            else:
                if trigger_warning:
                    self.output("{f} doesn't exist".format(f=path))
                return False
        except TypeError as e:
            self.output("path not given: {e}".format(e=e), level=logging.ERROR)

    def parse_yaml(self, cfg):
        """
        Return dict from yaml file
        :param cfg:
        :return:
        """
        _file = os.path.join(self.app_folder, cfg)
        if self.exists(_file, trigger_error=True):
            if self.check_extension(_file, "yaml"):
                self.output("[+] Reading values file: {f}".format(f=cfg), level=logging.DEBUG)
                with open(_file, 'r') as stream:
                    _cfg = yaml.load(stream)
                return _cfg

    def check_extension(self, _file, expected_ext, trigger_error=True):
        """
        Check file extension
        :param _file:
        :param expected_ext
        :param trigger_error
        :return:
        """
        file_name, file_extension = os.path.splitext(_file)
        try:
            if expected_ext not in file_extension:
                if trigger_error:
                    raise BadExtensionException(_file)
                else:
                    pass
            else:
                return True
        except BadExtensionException, e:
            self.output("File with extension {e} is expected, \"{g}\" given"
                        .format(e=expected_ext, g=e), logging.ERROR)

    @staticmethod
    def is_absolute(path):
        try:
            if len(path.split("/")) == 1:
                return False
            return True
        except AttributeError:
            return False

    def shell(self, cmd, strip=True):
        """
        write and return result of shell cmd
        :param cmd:
        :param strip:
        :return:
        """
        self.output('> {}'.format(cmd), level=logging.DEBUG)
        return self.tools.shell(cmd, strip)


if __name__ == "__main__":
    tools = Tools()
    my_cert = Certificate(tools.get_logger())
    print(my_cert.read_csv(_file="/Users/john/Desktop/cert/csv/bulk_enroll_devices.csv", absolute=True))
