'''
Cygwin installer builder
'''

# Python Modules
import urllib2
import subprocess
import tempfile
import atexit
import os
import sys
import shutil
import logging
import re
import json
import pprint
from collections import defaultdict
from optparse import OptionParser

# Settings
MANDATORY_PKGS = ['cygrunsrv', 'openssh', 'dos2unix']
MIRROR_LIST_URL  = 'https://cygwin.com/mirrors.lst'
DEFAULT_SETTINGS = {
    'installer': 'http://cygwin.com/setup-x86_64.exe',
    'mirror': 'http://mirror.isoc.org.il/pub/cygwin/',
    'makensis': r'c:\Program Files (x86)\NSIS\makensis.exe',
}

# OptionParser
cli_parser = OptionParser(usage='usage: %prog /path/to/settings.json')
cli_parser.add_option(
    '--verbose', dest='verbose', action='store_true', help='show more information', default=False
)
cli_parser.add_option(
    '--list', dest='mirrors', action='store_true', help='list cygwin mirrors', default=False
)
cli_parser.add_option(
    '--appendversion', dest='version', type='string', help='add a string to the package version CUSTOMVERSION-CYGWINVERSION', default=None
)

# Logging
log = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter(
        '%(asctime)s [%(levelname)s]: %(message)s',
        '%d-%m-%Y %I:%M:%S'
    )
)
log.addHandler(console_handler)
log.setLevel(logging.DEBUG)


class CygwinBuilderException(Exception):
    '''
    CygwinBuilder Base Exception
    '''
    pass


def cmd(command):
    '''
    Execute a command shell
    '''
    log.debug('executing command {0}'.format(' '.join(command)))
    proc = subprocess.Popen(
        command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None
    )
    proc_ret = proc.communicate()
    stdout = proc_ret[0]
    stderr = proc_ret[1]
    log.debug('{1} stdout:\n{0}'.format(stdout, command[0]))
    log.debug('{1} stderr:\n{0}'.format(stderr, command[0]))
    exit_code = proc.returncode
    if exit_code != 0:
        raise CygwinBuilderException(
            'command "{0}" returned with exit={1}\n{1}\n\n{2}'.format(' '.join(command), exit_code, stdout, stderr)
        )
    return proc_ret, stdout, stderr


def get_script_dir():
    '''
    Return the script directory
    '''
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def download_installer(url, dest, timeout=60):
    '''
    Download the cygwin installer
    '''
    
    for i in ['http://', 'https://', 'ftp://']:
        if url.startswith(i):
            log.info('downloading cygwin installer into "{0}"'.format(dest))
            response = urllib2.urlopen(url, timeout=timeout)
            with open(dest, 'wb') as f:
                f.write(response.read())
            return
    
    shutil.copy(url, dest)
    return


def create_temp_dir():
    '''
    Create a temp directory, cd into it and return the previous location
    '''
    log.info('creating temp directory')
    prev = os.getcwd()
    tmpdir = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, tmpdir)
    tmpdir = os.path.join(tmpdir, 'buildenv')
    log.info('temp directory = "{0}"'.format(tmpdir))

    shutil.copytree(
        os.path.join(get_script_dir(), 'buildenv'),
        tmpdir,
    )
    os.chdir(tmpdir)
    return prev, tmpdir


def get_mirrors():
    '''
    Returns list of the cygwin mirrors
    '''
    response = urllib2.urlopen(MIRROR_LIST_URL, timeout=5)
    ret = defaultdict(list)
    for line in response.read().splitlines():
        url, fqdn, continent, state = line.split(';')
        ret[continent].append(url)
    return ret


def install_cygwin_package(installer, pkgs, site):
    '''
    Run the cygwin installer to download cygwin
    and the required packages
    '''
    
    root_dir = os.path.join(os.path.abspath('.'), 'cygwin')

    for p in MANDATORY_PKGS:
        if not p in pkgs:
            pkgs.append(p)
    commmad = [
        installer,
        '--no-admin',
        '--no-shortcuts',
        '--quiet-mode',
        '--root',
        root_dir,
        '--site',
        site,
        '--packages',
        ','.join(pkgs),
    ]

    log.info('running cygwin installer')
    cmd(commmad)
    
    if pkgs:
        log.info('looking for installed packages')
        pkgs_set = set(pkgs)
        proc_ret, stdout, stderr = cmd([
            os.path.join(root_dir, 'bin', 'cygcheck.exe'),
            '--check-setup',
        ])
        stdout = stdout.splitlines()
        stdout.pop(0)
        stdout.pop(0)
        for line in stdout:
            pkg, version, state = line.split()
            try:
                pkgs_set.remove(pkg)
            except KeyError:
                pass
            if not pkgs_set:
                break
        if pkgs_set:
            miss = ','.join(pkgs_set)
            log.error('missing packages: {0}'.format(miss))
            raise CygwinBuilderException(
                'missing packages: {0}'.format(miss)
            )
    
    proc_ret, stdout, stderr = cmd([
        os.path.join(root_dir, 'bin', 'cygcheck.exe'),
        '--version',
    ])
    cygwin_version = stdout.splitlines()[0].split()[-1]
    cygwin_version.strip()
    log.info('Cygwin version is {0}'.format(cygwin_version))
    return cygwin_version, root_dir


def zip_cygwin(cygwin_path):
    '''
    Zip the Cygwin directory
    '''
    log.info('zipping {0}'.format(cygwin_path))
    saved_dir = os.getcwd()
    os.chdir(cygwin_path)
    proc_ret, stdout, stderr = cmd([
        os.path.join(saved_dir, '7z', '7z.exe'),
        'a', '-ssw', '-r', '-tzip',
        os.path.join(saved_dir, 'cygwin.zip'),
        '*',
    ])
    os.chdir(saved_dir)
    return True


def create_nsi_config(cygwin_version, template_file='Cygwin.nsi'):
    '''
    Create the NSI build file from the template
    '''

    log.info('compiling nsi file')
    ret = 'Cygwin-Compiled.nsi'
    template = open(template_file, 'r')
    nsi = open(ret, 'w')

    log.debug('-------------------------------')
    for line in template:
        new_line = re.sub('TMPL_MyCygwinVersion', cygwin_version, line)
        log.debug(new_line)
        nsi.write(new_line)
    log.debug('-------------------------------')
    
    template.close()
    nsi.flush()
    nsi.close()
    return ret


def make_installer(makensis, nsi):
    '''
    Make the custom windows installer via NSIS
    '''

    log.info('Creating the custom cygwin installer')
    proc_ret, stdout, stderr = cmd([makensis, nsi])

    pkg = None
    for line in stdout.splitlines():
        match = re.search('^Output: "(.*)"', line, re.M)
        if match:
            log.debug(line)
            pkg = match.group(1)
            log.info('installer name is: "{0}"'.format(pkg))
            break
    if not pkg:
        raise CygwinBuilderException(
            'could not find the name of the installer !'
        )
    return pkg


def main():
    '''
    Main
    '''
    
    opts, settings = parse_cmd_args()
    if opts.mirrors:
        print json.dumps(get_mirrors(), indent=4)
        exit(0)

    os.chdir(get_script_dir())
    prev_dir, tmpdir = create_temp_dir()
    try:
        installer_path = os.path.join(tmpdir, 'cygwin_installer.exe')
        download_installer(settings['installer'], installer_path)
        cygwin_version, cygwin_path = install_cygwin_package(
            installer_path,
            settings['packages'],
            settings['mirror'],
        )
        if opts.version:
            cygwin_version = '-'.join([opts.version, cygwin_version])
        nsi = create_nsi_config(cygwin_version)
        zip_cygwin(cygwin_path)
        pkg = make_installer(settings['makensis'], nsi)
        shutil.copy(pkg, prev_dir)
    except CygwinBuilderException as e:
        os.chdir(prev_dir)
        print 'Build Error:\n{0}'.format(e)
        exit(1)
    except Exception as e:
        os.chdir(prev_dir)
        raise e
    os.chdir(prev_dir)
    print 'Build Success: {0}'.format(os.path.join(prev_dir, os.path.basename(pkg)))
    exit(0)


def parse_cmd_args():
    '''
    Get the settings from the command line
    '''

    opts, args = cli_parser.parse_args()
    
    if opts.mirrors:
        return opts, None
    
    if len(args) != 1:
        cli_parser.print_help()
        exit(1)
    
    if opts.verbose:
        console_handler.setLevel(logging.DEBUG)
        log.debug('running in debug mode')
    
    try:
        with open(args[0], 'r') as f:
            settings = json.load(f) 
    except Exception as e:
        print 'Error reading json file "{0}"\n{1}\n'.format(args[0], e)
        cli_parser.print_help()
        exit(1)
    
    for key, value in DEFAULT_SETTINGS.iteritems():
        try:
            settings[key]
        except KeyError:
            log.warning('missing "{0}" using default "{1}"'.format(key, value))
            settings.update({key: value})
    
    log.debug(json.dumps(settings, indent=4))
    
    return opts, settings


if __name__ == '__main__':
    main()
