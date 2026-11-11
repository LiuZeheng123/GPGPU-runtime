from pathlib import Path
import hashlib, importlib.util, json, shutil, tarfile, zipfile

project=Path(__file__).resolve().parent/'GPGPU_U280_winter2026'
root=Path('/home/liuzeheng/gpgpu-c-20261111')
out=project/'results/c-runtime-suite-20261111'
out.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('verifier',project/'scripts/verify_ptx_suite_results.py')
verifier=importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
checks=[]
def copy(source,dest):
 dest.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(source,dest)
def zip_logs(source,dest):
 dest.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(dest,'x',zipfile.ZIP_DEFLATED) as z:
  for path in sorted(source.rglob('*')):
   if path.is_file():z.write(path,str(path.relative_to(source)))
for source in sorted((root/'evidence').iterdir()):
 if not source.is_dir():continue
 dest=out/source.name
 if source.name=='c-native-block32-v1':
  for path in source.glob('*.json'):copy(path,dest/path.name)
  for path in source.glob('*.cflags'):copy(path,dest/path.name)
  zip_logs(source/'logs',dest/'logs.zip')
  continue
 for path in source.rglob('*'):
  if not path.is_file() or 'cases' in path.relative_to(source).parts:continue
  copy(path,dest/path.relative_to(source))
 if (source/'cases').exists():
  directories=sorted((source/'cases').iterdir())
  for offset in range(0,len(directories),96):
   batch=directories[offset:offset+96]
   with tarfile.open(dest/('cases-'+batch[0].name+'-'+batch[-1].name+'.tgz'),'x:gz') as archive:
    for directory in batch:
     for path in sorted(directory.iterdir()):archive.add(path,arcname=str(path.relative_to(source)),recursive=False)
  checks.append(verifier.verify(dest))
for path in root.glob('*module*'):
 pass
for source in root.iterdir():
 if source.is_dir() and (source/'manifest.json').is_file():
  dest=out/'modules'/source.name
  manifest=json.loads((source/'manifest.json').read_text())
  names=set(manifest['files'])|{'manifest.json','build.json','compile.log'}
  for name in sorted(names):
   if (source/name).is_file():copy(source/name,dest/name)
 if source.is_dir() and source.name.startswith('binding-'):
  for path in source.iterdir():
   if path.is_file():copy(path,out/'bindings'/source.name/path.name)
for name in ['native-block32-driver.log']:
 copy(root/'evidence'/name,out/name)
copy(Path(__file__),out/'export-driver.py')
copy(project/'scripts/verify_ptx_suite_results.py',out/'verify-script.py')
final=json.loads((out/'c-final-checks-v1/result.json').read_text())
for name,digest in final['source_files'].items():assert hashlib.sha256((project/name).read_bytes()).hexdigest()==digest,name
assert sum(c['cases'] for c in checks)==1320
assert sum(c['block32_cases'] for c in checks)==120
(out/'verification.json').write_text(json.dumps(dict(status='PASS',runs=checks,total_cases=1320,block32_cases=120,recovery_runs=6,
 source_binding='All files recorded by final Linux regression match the current checkout',
 scope='archive readback and arithmetic consistency; not independent E acceptance'),indent=2)+'\n')
export={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}
(out/'export.json').write_text(json.dumps(dict(schema_version='c-suite-evidence-export-v1',files=export,
 capture_format='cases-*.tgz contain regular files under cases/<id>/; verify_ptx_suite_results.py reads without extraction',
 omitted='Native shared libraries, SDK and toolchain remain in the original Linux workspace; use recorded fixed versions and build commands'),indent=2)+'\n')
print(json.dumps({'status':'PASS','exported_files':len(export)+1,'bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'cases':1320,'block32_cases':120}))
