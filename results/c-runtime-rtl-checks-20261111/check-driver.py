from pathlib import Path
import hashlib,json,shutil,sys,tempfile
project=Path(__file__).resolve().parent/'GPGPU_U280_winter2026'
sys.path.insert(0,str(project/'scripts'))
from verify_ptx_suite_results import verify
from compare_ptx_backends import compare
evidence=project/'results/c-runtime-rtl-20261111'
manifest=json.loads((evidence/'export.json').read_text(encoding='utf-8'))
for name,expected in manifest['files'].items():assert hashlib.sha256((evidence/name).read_bytes()).hexdigest()==expected,name
legacy=[]
for p in sorted((project/'results/c-runtime-suite-20261111').glob('c-*/result.json')):
 data=json.loads(p.read_text(encoding='utf-8'))
 if data.get('schema_version')=='ptx-suite-simx-v1':legacy.append(verify(p.parent))
assert sum(r['cases'] for r in legacy)==1320
source=evidence/'c-copy-rtlsim-v1'
original=json.loads((source/'result.json').read_text(encoding='utf-8'))
temp_root=project/'tmp';temp_root.mkdir(exist_ok=True)
checks=[]
with tempfile.TemporaryDirectory(dir=temp_root) as folder:
 temp=Path(folder);assert temp.resolve().is_relative_to(temp_root.resolve())
 for file in source.glob('cases-*.tgz'):shutil.copyfile(file,temp/file.name)
 for mutation in ('wrong-capture-hash','duplicate-case','wrong-recovery-result','mixed-backend','wrong-legacy-schema','different-module','duplicate-backend'):
  data=json.loads(json.dumps(original))
  if mutation=='wrong-capture-hash':data['cases'][0]['files']['observed_z.bin']='0'*64
  if mutation=='duplicate-case':data['cases'].append(data['cases'][0])
  if mutation=='wrong-recovery-result':data['recovery']['observed_hex']='00000000'
  if mutation=='mixed-backend':data['cases'][0]['completion']['backend']='simx'
  if mutation=='wrong-legacy-schema':data['schema_version']='ptx-suite-simx-v1'
  if mutation=='different-module':data['module_manifest_sha256']='0'*64
  (temp/'result.json').write_text(json.dumps(data),encoding='utf-8')
  try:
   if mutation=='different-module':compare([evidence/'c-copy-simx-v1',temp,evidence/'c-copy-xrtsim-v1'])
   elif mutation=='duplicate-backend':compare([evidence/'c-copy-simx-v1',source,source])
   else:verify(temp)
  except (AssertionError,ValueError):checks.append(dict(mutation=mutation,status='REJECTED'))
  else:raise AssertionError('corruption accepted: '+mutation)
out=project/'results/c-runtime-rtl-checks-20261111';out.mkdir(exist_ok=False)
record=dict(status='PASS',scope='archive integrity, old-schema compatibility and deliberate corruption; not device execution',
 export_hashes=len(manifest['files']),checks=checks,legacy_cases=1320,legacy_checks=legacy,
 scripts={name:hashlib.sha256((project/'scripts'/name).read_bytes()).hexdigest() for name in ('verify_ptx_suite_results.py','compare_ptx_backends.py')})
(out/'result.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(__file__,out/'check-driver.py')
print(json.dumps(dict(status='PASS',export_hashes=len(manifest['files']),deliberate_corruptions_rejected=len(checks),legacy_cases=1320)))
