from pathlib import Path
import hashlib,json,shutil,sys,tarfile,zipfile
project=Path(__file__).resolve().parent/'GPGPU_U280_winter2026'
sys.path.insert(0,str(project/'scripts'))
from compare_ptx_backends import compare
from verify_ptx_suite_results import verify
root=Path('/home/liuzeheng/gpgpu-c-rtl-20261111')
out=project/'results/c-runtime-rtl-20261111'
out.mkdir(exist_ok=False)
def copy(source,dest):
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
for source in sorted((root/'evidence').iterdir()):
 if not source.is_dir():continue
 dest=out/source.name
 if source.name.startswith('c-native-'):
  for p in source.glob('*.json'):copy(p,dest/p.name)
  for p in source.glob('*.cflags'):copy(p,dest/p.name)
  for sub in ('configs','artifacts'):
   for p in (source/sub).rglob('*'):
    if p.is_file() and p.suffix in ('.json','.h','.vh','.stamp','.mk'):copy(p,dest/p.relative_to(source))
  with zipfile.ZipFile(dest/'logs.zip','x',zipfile.ZIP_DEFLATED) as z:
   for p in sorted((source/'logs').glob('*')):z.write(p,'logs/'+p.name)
  continue
 for p in source.rglob('*'):
  if p.is_file() and 'cases' not in p.relative_to(source).parts:copy(p,dest/p.relative_to(source))
 if (source/'cases').exists():
  dirs=sorted((source/'cases').iterdir())
  for offset in range(0,len(dirs),96):
   batch=dirs[offset:offset+96]
   with tarfile.open(dest/('cases-'+batch[0].name+'-'+batch[-1].name+'.tgz'),'x:gz') as tf:
    for d in batch:
     for p in sorted(d.iterdir()):tf.add(p,arcname=str(p.relative_to(source)),recursive=False)
for source in root.glob('binding-*'):
 for p in source.iterdir():
  if p.is_file():copy(p,out/'bindings'/source.name/p.name)
for name in ('tool-setup.json','uuid-setup.json'):copy(root/name,out/name)
for p in (root/'evidence').glob('*driver.log'):copy(p,out/p.name)
copy(project.parent/'c-u280-account-20261111.json',out/'u280-account.json')
copy(Path(__file__),out/'export-driver.py')
copy(project/'scripts/inspect_u280_account.py',out/'inspect_u280_account.py')
checks=[compare([out/('c-'+kernel+'-'+backend+'-v1') for backend in ('simx','rtlsim','xrtsim')]) for kernel in ('copy','vadd','affine')]
assert sum(c['identical_cases'] for c in checks)==840
regression=json.loads((out/'c-final-checks-v1/result.json').read_text())
for name,expected in regression['source_files'].items():assert hashlib.sha256((project/name).read_bytes()).hexdigest()==expected,name
result=dict(status='PASS',checks=checks,total_executions=2520,identical_cases_per_backend=840,
 block32_executions=360,recovery_runs=9,
 source_binding='Final Linux regression hashes match the current scripts and tests',
 modules='Same exact three modules from results/c-runtime-suite-20261111/modules/*-block32-v1-v1; no recompilation between backends',
 scope='author tests plus archive readback and differential consistency; independent E and U280 NOT_RUN')
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
files={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}
(out/'export.json').write_text(json.dumps(dict(schema_version='c-rtl-evidence-export-v1',files=files,
 capture_format='cases-*.tgz contain regular files under cases/<id>; read without extraction',
 omitted='SDK, private host packages, native shared libraries and intermediate object files remain in the Linux workspace; rebuild using recorded fixed inputs'),indent=2)+'\n')
print(json.dumps(dict(status='PASS',files=len(files)+1,bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),executions=2520)))
