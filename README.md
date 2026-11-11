# GPGPU Runtime：Vortex / PTX / U280

刘泽衡（[LiuZeheng123](https://github.com/LiuZeheng123)）的数字 GPGPU 项目工作仓库，保存 **C 分工：Runtime 与上板对接** 的代码、测试和实验记录。

目标是让受支持的 PTX 程序经过编译，在 Vortex GPGPU 上执行，并由主机程序写入输入、发起计算、等待完成和读回结果。当前已跑通 **PTX copy / vadd / affine → Vortex2 Runtime → SimX**，覆盖 16 线程基线和独立 32 线程候选；U280 实板对接仍待完成。

> 截至 2026-11-11：三类程序共 1320/1320 组 SimX 用例通过，6 次实际超时恢复通过。该阶段结果不代表完整 PTX/CUDA 兼容、独立验收或 U280 板上验证完成。

## 来源与协作关系

- 项目基于同学的 [Vortex-U280](https://github.com/slishysun974/Vortex-U280)，继承基线为 `46dd01406a98ee6eab451a435c8a761b4b6a9eea`。保留原有 A/B 平台、前端、文档及选定实验记录；这些历史成果不能全部归为本人的工作。
- 团队共享空间：[sunshawn-new/GPGPU_U280_winter2026](https://github.com/sunshawn-new/GPGPU_U280_winter2026)。本仓库保存个人进度，后续按团队约定同步 C 的改动；个人上传不等于团队已合并。
- 处理器上游：[vortexgpgpu/vortex](https://github.com/vortexgpgpu/vortex)，固定提交 `7fe19369587c087f902c3e2bc2add612aa910a95`；工具链 v3.0.1，固定提交 `8c64cf921d3c6c456e80f00d24482d0aa2153a82`。
- 当前方向为 Vortex 与 PTX P0 子集，不包含模拟电路。原项目、第三方源码及其许可证/署名保持各自归属，本仓库不额外授予第三方代码许可。

## 已完成的阶段成果

```text
PTX 源码 → 前端检查与代码生成 → 设备包装与编译 → kernel.vxbin
                                                       ↓
主机分配/写入数据 → Runtime 装载与启动 → SimX 执行 → 读回并核对
```

| 检查范围 | 实际结果 |
|---|---|
| 固定版本原生 SimX demo | PASS，输出 `PASSED!`，退出码 0 |
| 三类 PTX、两套配置的编译 | 6/6 PASS，分别生成 ELF、vxbin、反汇编；不混用运行库 |
| 16 线程基线（1c / 4w / 4t） | copy 96、vadd 96、affine 288，共 **480/480 PASS** |
| 32 线程候选（1c / 8w / 4t） | copy 168、vadd 168、affine 504，共 **840/840 PASS**；其中 block=32 为 120 组 |
| 超时恢复 | 6/6 实际超时后排空队列、失效旧句柄、重新分配并执行，PASS |
| Linux 回归测试 | **138 通过、14 跳过、0 失败**，跳过原因保留在日志 |
| 本阶段 PTX 的处理器 RTL / XRT AFU / U280 | **NOT_RUN**，未进行 E 分工的独立接收 |

用例覆盖 12 个数组长度、2 套输入、非零指针偏移、整个输入与输出分配区、哨兵和 u32 溢出；affine 另覆盖 alpha=0/1/0xffffffff。基线 block 为 1/4/7/16，候选另加 17/31/32。候选根配置与原基线分别保留，这不是 32-lane warp 兼容声明。

实际运行环境为本机 **Ubuntu 24.04 WSL、glibc 2.39、G++ 13.3、Python 3.12、CMake 3.31.10**。数字服务器原环境为 glibc 2.17，不能直接运行本次固定预编译工具链；本轮结果来自 WSL，没有执行 FPGA。记录的 H2D、launch、wait、D2H 和比较耗时是主机墙钟时间，包含仿真开销，不作板卡性能或两配置性能优劣结论。

## 从哪里看起

| 入口 | 内容 |
|---|---|
| [C 最新三类程序与 block32 验证](docs/C_RUNTIME_SUITE_20261111.md) | 1320 组用例、恢复、修复、耗时与复现 |
| [C 首条 SimX 链路](docs/C_RUNTIME_SIMX_20261110.md) | 11 月 10 日 vadd 的历史阶段结果 |
| [C 第一批记录](docs/C_RUNTIME_PROGRESS_20261110.md) | 模块包装与启动前检查 |
| [当前状态](docs/STATUS.md) / [项目交接](docs/PROJECT_HANDOFF.md) | 最新进展与历史状态，以顶部新记录为准 |
| [团队分工](docs/RESEARCH_PLAN.md) | A—E 分工与研究安排 |
| [合作接口](docs/COLLABORATION_PROTOCOL.md) | 参数、模块、资源与接收约定 |
| [PTX 子集规范](docs/PTX_COMPATIBILITY_PROFILE.md) | 白名单、语义和限制 |
| [本阶段证据](results/c-runtime-suite-20261111/) | 六组运行、六个模块、原始输入输出、失败记录与哈希 |

## 获取代码与运行检查

```bash
git clone https://github.com/LiuZeheng123/GPGPU-runtime.git
cd GPGPU-runtime
git submodule update --init upstream/vortex
git -C upstream/vortex submodule update --init third_party/softfloat third_party/ramulator2
python3 -B -m unittest discover -s tests -v
```

Windows 可用 `python` 替换 `python3` 运行宿主 Python 检查；设备编译与 SimX 使用兼容 Linux 环境。单测不等于设备执行；缺少编译器、上游源码或历史材料时，相关测试会跳过。运行原生 ABI 布局检查时，将 `VORTEX_SOURCE` 指向完整的固定 Vortex 源码目录，并提供 `g++`。

### 在已准备的 Linux 环境运行 PTX vadd

先准备固定工具链、Ramulator 依赖以及通过原生 smoke 的 SimX 构建。入口分别是 `scripts/prepare_toolchain.py`、`scripts/native_dependencies.py` 和 `scripts/run_native_smoke.py`，参数可用 `--help` 查看。不同配置使用独立构建目录。

下面假定 `RUN_ROOT` 内已有 `tools/`、`build-native/` 和 `evidence/native/summary.json`，来自本仓库 lock 指定版本及 `configs/native_smoke.json`。请修改路径，且输出目录 `module-vadd`、`build-vadd`、`binding`、`evidence/ptx-vadd` 必须尚不存在。

```bash
export RUN_ROOT=/absolute/path/to/your/linux-workspace
export VORTEX_SOURCE="$PWD/upstream/vortex"

python3 -B scripts/ptx_module.py prepare ptx/samples/vadd_u32.ptx \
  --output "$RUN_ROOT/module-vadd" \
  --hardware configs/native_smoke.json --target-lock configs/target_lock.json
python3 -B scripts/ptx_module.py build "$RUN_ROOT/module-vadd" \
  --vortex-source "$VORTEX_SOURCE" --build-root "$RUN_ROOT/build-vadd" \
  --tooldir "$RUN_ROOT/tools" --target-lock configs/target_lock.json
python3 -B scripts/bind_simx_runtime.py \
  --summary "$RUN_ROOT/evidence/native/summary.json" \
  --hardware configs/native_smoke.json --target-lock configs/target_lock.json \
  --output "$RUN_ROOT/binding"

export VORTEX_DRIVER=simx
export VORTEX_PROFILING=0
export LD_LIBRARY_PATH="$RUN_ROOT/build-native/sw/runtime${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
python3 -B scripts/run_ptx_suite.py --kernel vadd \
  --module "$RUN_ROOT/module-vadd" --binding "$RUN_ROOT/binding/binding.json" \
  --target-lock configs/target_lock.json --output "$RUN_ROOT/evidence/ptx-vadd"
```

copy/affine 分别使用对应的 PTX 源文件、独立 module/build/output 目录及 `--kernel copy` / `--kernel affine`。32 线程需先以 `run_native_smoke.py --target-profile block32-v1` 构建独立运行库，再统一使用 `configs/candidates/block32-v1/` 下的 lock 和硬件配置构建模块、生成 binding；详见 [本轮复现](docs/C_RUNTIME_SUITE_20261111.md)。

归档的 binding 包含原执行环境绝对路径和库哈希，**不能直接用于另一台机器**；新环境需重新构建并生成 binding。

## 核心目录

```text
scripts/ptx_frontend.py      PTX 解析、检查与代码生成
scripts/ptx_module.py        设备包装、编译与模块校验
scripts/ptx_launch.py        参数和 buffer 生命周期检查
scripts/ptx_runtime.py       真实 Vortex2 API、队列和资源管理
scripts/bind_simx_runtime.py 构建、配置与动态库身份绑定
scripts/run_ptx_simx.py      实际执行与结果捕获
scripts/run_ptx_suite.py     三类 PTX、两套配置、拒绝/恢复和耗时记录
scripts/verify_ptx_suite_results.py  从归档原始字节重新计算并核对结果
ptx/samples/                PTX 示例
configs/                    固定版本、ABI 与硬件配置
tests/                      宿主单测和 ABI 检查
docs/                       分工、接口、状态与交接
results/                    按运行编号保存的实验记录
upstream/vortex/            固定上游 Git 子模块
```

每批结果的 `export.json` 保存导出文件 SHA-256。11 月 11 日的 `cases-*.tgz` 分块保存原始 `cases/<id>/` 文件，旧批次的 `cases.zip` 保持原样；失败尝试也保留。完整 SDK、工具链缓存、动态库和大型 FPGA 产物按固定版本重建，不放入 Git。部分同学历史材料由原工作区保存，详见[历史证据索引](results/README.md)。

只核对归档（不需要 Vortex 工具链，也不等于重新执行设备）：

```bash
python3 -B scripts/verify_ptx_suite_results.py results/c-runtime-suite-20261111/c-affine-block32-v1-v1
```

## 当前限制与下一步

- Runtime 当前接通 SimX，单队列、单任务在途；本轮按每个 context 一个模块验证。
- 恢复证明的是 SimX 队列排空与资源重建，未证明设备硬复位、故障 abort 或 PCIe/DMA 隔离。
- 下一步由 E 使用独立答案接收三类 PTX 与 block32 候选；与 A/B 对接 PTX 的 RTL/AFU 与 U280 运行。当前尚无这些后端的本轮 PTX 结果。
- A/B 历史 FPGA 构建和时序材料为参考成果；HOST 通路、平台约束与板上结果仍按团队最新证据接收。

## 后续保存与同步

个人开发分支为 `c/liuzeheng-runtime`。提交说明改动、命令、结果和验证范围；新实验写入新的 `results/<run_id>/`，不改写旧证据。向团队同步前先对齐共享仓库最新基线，再提交 C 分工的改动供审阅。

仓库只保存项目文件；服务器密码、API key、个人 SSH 配置和工具链缓存不应提交。
