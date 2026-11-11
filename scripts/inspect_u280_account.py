"""Read-only inspection of current-account artifacts and visible U280 status.

No device open, programming, reset, HOST configuration or privilege escalation.
KDS snapshots do not reserve a card or prove all users' file handles are absent.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess


def collect():
    home=Path.home()
    root=home/'gpgpu_work'
    result=dict(schema_version='c-u280-account-inspection-v1',
        collected_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope=__doc__,device_open='NOT_RUN',board_execution='NOT_RUN',
        device_reservation='NOT_CONFIRMED',project_root='~/gpgpu_work',artifacts=[],cards=[],commands=[])
    if root.is_dir():
        for directory, folders, files in os.walk(str(root),followlinks=False):
            folders[:]=[f for f in folders if f not in ('.git','node_modules','__pycache__')]
            for name in files:
                if name.endswith('.xclbin') or name in ('libvortex.so','libvortex-xrt.so'):
                    path=Path(directory)/name
                    result['artifacts'].append(dict(path='~/'+str(path.relative_to(home)),bytes=path.stat().st_size,
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    for device in sorted(Path('/sys/bus/pci/drivers/xocl').glob('*:*')):
        card=dict(bdf=device.name,observations={})
        for name in ('ready','host_mem_size','interface_uuids','kdsstat'):
            try:card['observations'][name]=(device/name).read_text().strip()
            except OSError as exc:card['observations'][name]=dict(error=type(exc).__name__)
        card['render_nodes']=[]
        for node in sorted((device/'drm').glob('renderD*')):
            path=Path('/dev/dri')/node.name
            card['render_nodes'].append(dict(path=str(path),readable=os.access(str(path),os.R_OK),writable=os.access(str(path),os.W_OK)))
        result['cards'].append(card)
    for name,argv in [('glibc',['getconf','GNU_LIBC_VERSION']),
                      ('compiler',['/opt/rh/devtoolset-9/root/usr/bin/g++','--version']),
                      ('xrt',['/opt/xilinx/xrt/bin/xbutil','--version'])]:
        try:
            p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)
            result['commands'].append(dict(name=name,argv=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
        except (OSError,subprocess.TimeoutExpired) as exc:
            result['commands'].append(dict(name=name,argv=argv,error=type(exc).__name__))
    result['status']='COLLECTED'
    return result


if __name__=='__main__':
    print(json.dumps(collect(),indent=2))
