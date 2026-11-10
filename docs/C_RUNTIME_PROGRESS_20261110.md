# C：Runtime 第一批实现与交接

本页保留第一批宿主验证记录。后续已完成真实 PTX vadd SimX 96/96 与超时排空恢复，最新状态见 [第二批交接](C_RUNTIME_SIMX_20261110.md)。

作者账户：LiuZeheng123。开发分支：`c/liuzeheng-runtime`。
团队工作仓库：`sunshawn-new/GPGPU_U280_winter2026`。
参考基线：`slishysun974/Vortex-U280@46dd01406a98ee6eab451a435c8a761b4b6a9eea`。
本文及实现位于本机和本人服务器账户，尚未推送共享 GitHub 仓库；检查时该仓库仍为空。

## 这批工作解决什么

D 的前端已经能把 PTX 变成 C++ 计算逻辑，但此前没有项目设备入口和启动参数检查。C 的这批实现把这两个接口接起来，供后续真正的 Vortex 编译、SimX 和板卡适配使用。

- `scripts/ptx_module.py`：生成 Vortex2 `kernel_main` 包装，映射四个逻辑线程寄存器，保留 D 的参数布局和谓词语义；产出绑定 target lock 的模块清单。使用固定上游 SIMT Makefile 的编译入口，在新目录构建并记录日志；核对固定工具链文件哈希。加载前校验源代码/生成物、布局、目标、文件哈希、ELF 类型和 vxbin 入口/范围。
- `scripts/ptx_launch.py`：设备地址登记、buffer+offset+声明范围的参数检查、小端参数快照、单任务在途占用、提交时再次检查句柄、隔离后全量失效。它是供后端调用的元数据组件，不是设备内存分配器，也没有模拟执行 kernel。
- `tests/test_ptx_module.py`：文件损坏、重新计算哈希后的错误生成代码、路径、布局、目标、容量、失效句柄、重复启动等拒绝测试；三个样例的设备包装在宿主串行测试夹具中运行。

原始前端的 `loadable=false` 约定、默认 lock、B=32 候选及全部历史证据未修改。项目模块使用独立 `ptx-vx-module-v1-draft`；默认 smoke 上限由 4 warps × 4 threads 得到 16，B=32 必须明确选择候选，不能冒充默认配置支持。

## 本轮真实验证

最终记录：`results/c-module-20261110-v2/`。Linux Python 3.11.13 / G++ 9.3.1。

- 仓库 Python 回归：136 项，122 通过、14 跳过、0 失败，退出码 0。跳过项在完整日志中列出，主要依赖公开快照未附带的源码/历史产物。
- 新增 C 测试：18 项全部通过，其中一个宿主 C++ 测试包含 3 kernels × 7 个 N × 4 个 block = 84 组执行；覆盖 N=0、尾线程、跨 block、非零偏移、u32 溢出、输入及输出哨兵。N=0 使用空指针检验假谓词不访问内存。
- `prepare` 生成 vadd 模块源文件成功；直接 `validate` 正确返回 `E_MODULE_NOT_BUILT`、退出码 1，没有把尚未编译的源码包当成设备镜像。
- v1 记录保留。v2 加入构建证据与 ELF 类型检查及禁止覆盖已有失败构建的测试，再跑回归。

宿主夹具使用测试专用线程寄存器头文件、串行调用包装函数。这证明包装/参数/内存结果在宿主模型上的行为，不证明 Vortex SIMT 编译、分歧收敛、RTL 或硬件线程调度。

## 复现入口

在项目根目录使用 Python 3.11+：

```sh
python -B -m unittest discover -s tests -v
python scripts/ptx_module.py prepare ptx/samples/vadd_u32.ptx \
  --output build/vadd-source-001 \
  --target-lock configs/target_lock.json --hardware configs/native_smoke.json
```

固定 Vortex 源码和工具链准备好后，编译命令如下。三个路径应为 Linux 无空格绝对路径，`--build-root` 必须不存在；编译失败保留目录，重新 prepare 到新目录后重试。

```sh
python scripts/ptx_module.py build build/vadd-source-001 \
  --target-lock configs/target_lock.json \
  --vortex-source /path/to/pinned/vortex \
  --tooldir /path/to/pinned/tools --build-root /path/to/new/build
python scripts/ptx_module.py validate build/vadd-source-001 \
  --target-lock configs/target_lock.json
```

编译入口尚未在完整固定工具链上执行；这是可审阅实现，不能当作已验证的 native 构建流程。宿主机器有 G++ 不代表具备 Vortex clang++。

## 接下来 C 继续做

1. 在本人账户准备固定 Vortex v3.0 源码及 v3.0.1 工具链，完成真实 SIMT 编译、反汇编核查和 vxbin 校验。现账户尚无这些完整构建依赖，无需用户另找课程材料。
2. 将项目层封装接到 `vortex2` 的实际 buffer/module/queue/event API，绑定实际 backend 与 target 配置。当前登记/占用组件要求后端串行调用，不能声称已有完整、并发安全的 runtime。
3. 首先跑 PTX vadd 的真实 SimX，再扩展 copy/affine、处理器 RTL 与 E 的独立测试。板卡连接需与 B 的实际镜像、HOST 通路和时序约束结论对齐。

超时恢复、设备故障、最终写入可见性、模块资源占用、设备关闭尚待原生后端接入。`complete` 和 `invalidate_after_isolation` 是可信后端的内部通知钩子，不可把用户传入一个布尔值当成真实设备完成或隔离。声明访问范围也不是任意 kernel 的内存沙箱。

本轮 **Vortex native build / PTX-SimX / PTX-RTL / U280 / E 独立验收均为 NOT_RUN**。未配置、加载或占用 FPGA 卡，未使用其他同学的私有文件或凭据。
