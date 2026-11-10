# C：PTX vadd 已接通真实 SimX

2026-11-10 第二批，LiuZeheng123，分支 `c/liuzeheng-runtime`。

现在已经实际跑通：PTX 源码 → 项目前端 → Vortex SIMT 编译 → vxbin → 项目 Runtime → SimX → 读回数据并比较。这个结果证明第一条软件联调链路可用；没有运行处理器 RTL、XRT AFU 模型或 U280 板卡，也不是 E 的独立验收。

## 结果与证据

证据根目录为 [`results/c-runtime-simx-20261110/`](../results/c-runtime-simx-20261110/)。导出文件哈希见其中 `export.json`，每份 `cases.zip` 解压后恢复原来的 `cases/` 树，原始 result.json 未改写。

| 实际检查 | 结果 | 证据 |
|---|---|---|
| 固定源码与依赖 | Vortex `7fe1936`、softfloat/ramulator 固定提交，源清单零差异 | `native-simx/summary.json`、`source_manifest.json` |
| 固定工具链 | v3.0.1 的 15 个分卷/单包 Git blob 与重组归档已核对；Clang 20.1.8 / RISC-V GCC 12.2.0 | `preparation/*download-v2*`、`*extract-v2*` |
| 上游原生 demo | PASS，命令退出 0，日志 `PASSED!` | `native-simx/logs.zip` |
| PTX vadd 真正编译 | PASS，三个构建命令退出 0；生成 ELF/vxbin/反汇编 | `vadd-module-v2/` |
| Vortex 特性 | 反汇编有 `vx_split_n` / `vx_join`，使用固定 `+xvortex` 工具链 | `vadd-module-v2/program.disasm`、`compile.log` |
| PTX vadd SimX | **96/96 PASS**，最后一次退出 0 | `c-ptx-vadd-simx-v3/result.json`、`cases.zip` |
| 实际超时与恢复 | `E_TIMEOUT` → 保留资源 → 排空队列 → generation 0→1 → 旧句柄拒绝 → 新分配/新装载计算 PASS | 同一 `result.json` 的 `recovery` |
| Runtime ABI 与回归 | 144 项：**130 PASS、14 SKIP、0 FAIL**，退出 0；真实头文件编译确认 ctypes 布局 | `c-runtime-closeout-v1/unittests.log` |
| 最终代码与实际执行绑定 | PASS，代码快照、哈希及实际 stdout 已保存 | `c-runtime-closeout-v2/` |

96 组用例由 12 个数组长度（0/1/7/15/16/17/31/32/33/65/257/1024）、4 个 block 大小（1/4/7/16）、两套输入组成。相同 buffer/module/queue 连续复用，比较整个输入及输出分配，涵盖不同非零偏移、尾部哨兵和 u32 溢出。超时后的额外计算验证 `0xffffffff + 2 == 1`。B=17 的启动和在途 free/unload/read/close 均正确拒绝。

14 个 SKIP 是参考快照未附带的历史文件、报告或默认位置的上游源码等条件；原因逐项保留在测试日志，未把跳过算作通过。宿主单测、原生 demo、PTX-SimX 三层分开记录。

## 实现变更

- `ptx_runtime.py` 通过固定 `vortex2.h` ABI 调用真实运行库，包含 alloc/write/load/launch/wait/read/free/unload/close 与有界排空恢复。按 context 串行调用，运行中和恢复状态限制资源操作；运行器明确启用 SimX，不支持的 backend 返回不可用，不作 CPU fallback。
- `bind_simx_runtime.py` 只接收真正通过 native smoke 的构建，绑定目标配置、三份主库及本地动态依赖的哈希。加载后再次检查实际库路径、线程/warp/core/cluster/XLEN。binding v2 也覆盖 Ramulator 动态库。
- `run_ptx_simx.py` 保留输入、预期值、读回原始字节、错误和恢复结果；最后版将仿真工作目录切到本次结果目录，Ramulator 不再向源码根目录写统计日志。
- 前端生成器升为 `ptx-vx-frontend-v1.1`：为 PTX 允许的未使用参数/寄存器加 C++17 `[[maybe_unused]]` 声明，解决真正编译时的 unused-variable 错误。未初始化值仍不初始化，PTX profile、ABI、白名单、计算及谓词语义未改变。宿主包装编译测试也启用了 `-Wall -Wextra -Werror`。

首次构建 `vadd-module-v1` 的失败日志保留。原整文件下载多次超时，之后使用有 Content-Range 检查的分段传输并验证所有 Git blob；旧下载已中止且无遗留进程，旧 summary 的未终结快照保留，以 v2 完整下载/解压记录为准。首次准备驱动遗漏 `--download` 的退出 2 也保留。ABI 测试初版有 printf 格式字符串转义错误，修正后编译头文件检查通过。

## 环境与复现

真实构建/执行位于本机已有的 **Ubuntu-24.04 WSL**：glibc 2.39、G++ 13.3、Python 3.12、独立 CMake 3.31.10。固定工具链需要 glibc ≥2.35，新数字服务器为 glibc 2.17，所以这次在兼容的 WSL 完成 SimX，没有替换服务器系统库。

Linux 独立目录 `/home/liuzeheng/gpgpu-c-20261110` 保留固定源码、完整工具链、构建目录和运行库；项目源文件仍以本机共享仓库 checkout 为准。当前 binding 的绝对库路径属于这套 Linux 构建，不能直接用于 CentOS 或声称可在服务器执行。

已有环境重跑（在项目根目录，输出目录需取新名字）：

```sh
export VORTEX_DRIVER=simx
export VORTEX_PROFILING=0
export LD_LIBRARY_PATH=/home/liuzeheng/gpgpu-c-20261110/build-native-simx-v1/sw/runtime
python3 -B scripts/run_ptx_simx.py \
  --module /home/liuzeheng/gpgpu-c-20261110/vadd-module-v2 \
  --binding /home/liuzeheng/gpgpu-c-20261110/runtime-binding-v2/binding.json \
  --target-lock configs/target_lock.json --output /path/to/new/run
```

从新环境开始时依次使用现有 `prepare_toolchain.py`、`native_dependencies.py`、`run_native_smoke.py`，然后 `ptx_module.py prepare/build`、`bind_simx_runtime.py` 和上述执行入口。每个脚本都有 `--help`；固定源码和工具链由 lock 指定，不能改成最新版本混用。

## 接收边界与下一步

当前是单队列、单任务在途的 SimX runtime 草案。本轮按每个 context 一个模块验收，模块内部任意越界访存不受软件参数检查保护。恢复仅证明 **SimX 的队列排空和重新分配**，没有证明故障设备重置、安全 abort、PCIe/DMA 隔离或 FPGA 恢复。

下一步依次接收 copy/affine 的真实 PTX 执行、block32 候选与 E 的独立用例，再对接 B 的 U280 平台。当前默认仍是 RV64 / 1c / 4w / 4t，不能把 16 线程 block 的成功算作 B=32 验收。板卡 HOST/时序等事项仍按 B 的当前证据处理。

本批代码与结果保存在本地 C 分支及本人服务器账户，个人 GitHub 归档地址为 [LiuZeheng123/GPGPU-runtime](https://github.com/LiuZeheng123/GPGPU-runtime)。项目入口、来源和复现说明见根目录 README；尚未推送或合并到团队共享仓库。
