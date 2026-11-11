from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, time

project=Path(__file__).resolve().parent/'GPGPU_U280_winter2026'
old=Path('/home/liuzeheng/gpgpu-c-20261110')
root=Path('/home/liuzeheng/gpgpu-c-20261111')
profile=sys.argv[1]
assert profile in ('smoke','block32-v1')
suffix=sys.argv[2] if len(sys.argv)>2 else 'v1'
out=root/'evidence'/('c-suite-'+profile+'-'+suffix)
out.mkdir(exist_ok=False)
config=project/('configs' if profile=='smoke' else 'configs/candidates/block32-v1')
native=(old/'evidence/c-native-simx-v1/summary.json' if profile=='smoke' else root/'evidence/c-native-block32-v1/summary.json')
summary=json.loads(native.read_text())
assert summary['status']=='PASS'
lib=Path(summary['build_path'])/'sw/runtime'
env=dict(os.environ,PATH=str(old/'host-tools/cmake-3.31.10-linux-x86_64/bin')+':'+os.environ['PATH'],
 CCACHE_DISABLE='1',VORTEX_SOURCE=str(old/'vortex'),VORTEX_DRIVER='simx',VORTEX_PROFILING='0',LD_LIBRARY_PATH=str(lib))
record=dict(status='RUNNING',profile=profile,commands=[],source_files={})
files=['scripts/ptx_frontend.py','scripts/ptx_module.py','scripts/ptx_launch.py','scripts/ptx_runtime.py',
 'scripts/run_ptx_simx.py','scripts/run_ptx_suite.py','scripts/bind_simx_runtime.py','tests/test_ptx_runtime.py','tests/test_ptx_suite.py']
for name in files:
 data=(project/name).read_bytes()
 record['source_files'][name]=hashlib.sha256(data).hexdigest()
 dest=out/'implementation'/name
 dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_bytes(data)
shutil.copyfile(__file__,out/'driver.py')
def save(): (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
def run(name,command):
 argv=[str(x) for x in command]
 start=time.perf_counter()
 with (out/(name+'.log')).open('xb') as log:
  result=subprocess.run(argv,cwd=project,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
 record['commands'].append(dict(name=name,argv=argv,exit_code=result.returncode,host_seconds=time.perf_counter()-start,log=name+'.log'))
 save()
 print(profile,name,'EXIT',result.returncode,flush=True)
 if result.returncode:raise RuntimeError(name+' failed')
save()
try:
 binding=root/('binding-'+profile+'-'+suffix)
 run('binding',[sys.executable,'-B','scripts/bind_simx_runtime.py','--summary',native,'--target-lock',config/'target_lock.json','--hardware',config/'native_smoke.json','--output',binding])
 for kernel in ('copy','vadd','affine'):
  module=root/(kernel+'-'+profile+'-'+suffix)
  run(kernel+'-prepare',[sys.executable,'-B','scripts/ptx_module.py','prepare','ptx/samples/'+kernel+'_u32.ptx','--output',module,'--hardware',config/'native_smoke.json','--target-lock',config/'target_lock.json'])
  run(kernel+'-build',[sys.executable,'-B','scripts/ptx_module.py','build',module,'--vortex-source',old/'vortex','--build-root',root/('build-'+kernel+'-'+profile+'-'+suffix),'--tooldir',old/'tools','--target-lock',config/'target_lock.json'])
  run(kernel+'-simx',[sys.executable,'-B','scripts/run_ptx_suite.py','--kernel',kernel,'--module',module,'--binding',binding/'binding.json','--target-lock',config/'target_lock.json','--output',root/'evidence'/('c-'+kernel+'-'+profile+'-'+suffix)])
 record['status']='PASS'
except Exception as exc:
 record.update(status='FAIL',error=str(exc))
finally:save()
sys.exit(0 if record['status']=='PASS' else 1)
