from pathlib import Path
import hashlib, importlib.util, json, shutil, tempfile
project=Path(__file__).resolve().parent/'GPGPU_U280_winter2026'
evidence=project/'results/c-runtime-suite-20261111'
manifest=json.loads((evidence/'export.json').read_text(encoding='utf-8'))
for name,digest in manifest['files'].items():assert hashlib.sha256((evidence/name).read_bytes()).hexdigest()==digest,name
spec=importlib.util.spec_from_file_location('verify',project/'scripts/verify_ptx_suite_results.py')
verify=importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)
source=evidence/'c-copy-smoke-v2'
original=json.loads((source/'result.json').read_text(encoding='utf-8'))
temp_root=project/'tmp'
temp_root.mkdir(exist_ok=True)
checks=[]
with tempfile.TemporaryDirectory(dir=temp_root) as folder:
 temp=Path(folder)
 assert temp.resolve().is_relative_to(temp_root.resolve())
 for file in source.glob('cases-*.tgz'):shutil.copyfile(file,temp/file.name)
 for mutation in ('wrong-capture-hash','duplicate-case','wrong-recovery-result'):
  data=json.loads(json.dumps(original))
  if mutation=='wrong-capture-hash':data['cases'][0]['files']['observed_z.bin']='0'*64
  if mutation=='duplicate-case':data['cases'].append(data['cases'][0])
  if mutation=='wrong-recovery-result':data['recovery']['observed_hex']='00000000'
  (temp/'result.json').write_text(json.dumps(data),encoding='utf-8')
  try:verify.verify(temp)
  except AssertionError:checks.append(dict(mutation=mutation,status='REJECTED'))
  else:raise AssertionError('corruption accepted: '+mutation)
out=project/'results/c-runtime-suite-checks-20261111'
out.mkdir(exist_ok=False)
record=dict(status='PASS',scope='archive integrity and deliberate corruption checks, not device execution',
 export_hashes=len(manifest['files']),checks=checks,verifier_sha256=hashlib.sha256((project/'scripts/verify_ptx_suite_results.py').read_bytes()).hexdigest())
(out/'result.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(__file__,out/'check-driver.py')
print(json.dumps(record))
