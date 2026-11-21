# 用同一块设备内存串联 vadd 和 affine

2026-11-21，C 分工。本示例演示应用怎样把一个 PTX 模块的输出交给下一个模块。两个模块共用一个 Runtime context。主机先写入输入和保护字，执行 `temp = x + y` 并等待完成，再卸载 vadd、装入 affine，让它读取同一个 temp 缓冲区，执行 `out = alpha * temp + y`。主机在两步都完成后才读回四个数组。所有运算按无符号 32 位取模。

| 后端 | 双算子用例 | 算子启动 | 退出码 |
|---|---:|---:|---:|
| SimX | 5/5 | 10 | 0 |
| 处理器 RTL | 5/5 | 10 | 0 |
| AFU RTL（XRTSIM） | 5/5 | 10 | 0 |

每路执行长度 0、1、32、33、65，使用 32 线程配置。每个缓冲区留有两个前置和三个后置保护字。验证逐字检查两个输入、临时数组、最终数组及所有保护字。每个后端的 JSON 保存两步完成事件、完整读回值、模块与运行库绑定的哈希。项目当前支持单模块装载，示例在每步结束后切换模块。本次范围为本地仿真，个人 U280 实板复现仍暂缓。

## 在已有 Linux 仿真环境运行

使用与 [11 月 11 日模块构建说明](../../docs/C_RUNTIME_SYNC_20261111.md) 一致的 block32 目标。先把 `MODULES` 设成含已构建 `vadd/` 和 `affine/` 的目录，把 `BINDING` 设为当前机器对应后端的 `binding.json` 绝对路径。例子使用 SimX。切换后端时，同时更换绑定和 `BACKEND`。

```bash
export BACKEND=simx
export VORTEX_DRIVER="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["driver"])' "$BINDING")"
export LD_LIBRARY_PATH="$(python3 -c 'import json,sys,pathlib; p=pathlib.Path(sys.argv[1]); print((p.parent/json.loads(p.read_text())["library_dir"]).resolve())' "$BINDING")${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
python3 -B scripts/run_ptx_chain.py --backend "$BACKEND" \
  --modules "$MODULES" --binding "$BINDING" \
  --target-lock configs/candidates/block32-v1/target_lock.json \
  --output "/tmp/vadd-affine-$BACKEND.json"
```

输出文件须使用新文件名。其他两个后端为 `rtlsim`、`xrtsim`。复核原始记录可直接打开 [SimX](simx.json)、[处理器 RTL](rtlsim.json)、[AFU RTL](xrtsim.json) 和 [进程退出码](runs.json)。接新算子时，可参考 [示例源码](../../scripts/run_ptx_chain.py) 的两次 launch，按新 PTX 的参数声明传入缓冲区、长度与标量，并提供对应的预期输出。
