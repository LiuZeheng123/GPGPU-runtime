# C：PTX 处理器 RTL、AFU 与上板交接

日期：2026-11-11。范围：C 的模块/Runtime 集成与作者测试；独立 E 接收和 U280 实板执行单独验收。

## 版本与实现

固定 Vortex `7fe19369587c087f902c3e2bc2add612aa910a95`、工具链 `8c64cf921d3c6c456e80f00d24482d0aa2153a82`、Verilator 5.050。原有根 lock/caps、上游源码与旧结果保留。采用独立 `configs/candidates/block32-v1`：RV64、1 cluster、1 core、8 warps、4 threads。

`ptx_runtime.py` 新增显式 `rtlsim` 和 `xrtsim`，保持单队列、单模块、单任务在途。`xrtsim` 对应驱动名 `xrt`，但只允许绑定已通过原生示例的 **NOXRT/XRTSIM AFU 模型**；没有启用物理 `xrt` 后端，也没有厂商 `hw_emu` 结果。

新增 `ptx-vx-runtime-binding-v3`：检查执行摘要、目标哈希、三个动态库、依赖和实际加载路径。AFU 绑定还检查 `-DXRTSIM`、`-DNOXRT` 构建标记；缺少证明、后端错配或库哈希改变，在装载前拒绝。既有 v2 仅保留 SimX 接收，旧证据不重写。PTX/参数 ABI 没有变化。

`run_ptx_suite.py --backend simx|rtlsim|xrtsim` 使用 `ptx-suite-simulation-v2` 结果格式。`verify_ptx_suite_results.py` 仍可读取旧 SimX 记录；`compare_ptx_backends.py` 比较三个后端是否使用同一目标、同一模块和逐字节相同的输入/输出。

## 运行与证据

| 后端 | copy | vadd | affine | 实际超时恢复 |
|---|---:|---:|---:|---:|
| SimX（新 Runtime 回归） | 168/168 | 168/168 | 504/504 | 3/3 |
| 处理器 RTL | 168/168 | 168/168 | 504/504 | 3/3 |
| NOXRT/XRTSIM AFU RTL 模型 | 168/168 | 168/168 | 504/504 | 3/3 |

本轮 **2520/2520 次执行 PASS**：同一组 840 个用例在三个后端分别执行，其中每路 120 个 block=32 用例。三个后端使用上一批三个 block32 模块的原始字节。每次运行额外检查 19 个拒绝场景，实际零等待触发 native status=7 后，排空、失效旧句柄、重新装载和计算均通过。所有运行退出 0。

覆盖长度 0/1/7/15/16/17/31/32/33/65/257/1024，block 1/4/7/16/17/31/32，两组输入与非零指针偏移；affine 的 alpha 为 0/1/0xffffffff。检查整个输入、输出及哨兵分配区；记录主机耗时，不把它解释为 FPGA 周期或吞吐量。

证据目录：[c-runtime-rtl-20261111](../results/c-runtime-rtl-20261111/)。`c-<kernel>-<backend>-v1` 保存结果与分块原始字节，`c-suite-*` 保存运行命令和实现快照，`bindings/` 保存三套绑定，`c-native-rtlsim-v1` 与 `c-native-xrtsim-v2` 保存原生通过记录，`c-native-xrtsim-v1` 保留首次失败。模块位于[上一批模块目录](../results/c-runtime-suite-20261111/modules/)，本轮不重新编译或改写。

归档核对器验证每个文件哈希、重新计算整数答案，并比较三个后端的原始输入、期望/实际输出和哨兵完全相同。这个比较由作者完成，不代替 E 的独立接收。损坏哈希、重复用例、错误恢复值、后端混用、错误旧 schema、不同模块和重复后端共七类故意破坏另做拒绝检查；旧 1320 组 SimX 归档仍能由新核对器读取。见[归档核验](../results/c-runtime-rtl-checks-20261111/result.json)。

Linux 完整回归：157 项中 **143 通过、14 跳过、0 失败**，退出 0；包含实际 Vortex2 头文件的 ABI 编译核验。跳过项目需要历史 FPGA 材料或特定上游检出，详见日志，不能算作通过。

运行环境为 Ubuntu 24.04 WSL / glibc 2.39 / G++ 13.3 / Python 3.12 / CMake 3.31.10，编译并行度为 2。ccache 4.9.1、libhiredis 1.2.0 与 UUID 头文件均由 Ubuntu 包下载后解包到项目私有目录，包 SHA-256 与 APT 元数据核对。Verilator 分片核对固定 Git blob，合并后核对固定 tar SHA-256 和二进制 SHA-256。

AFU 首次构建 `c-native-xrtsim-v1` 因缺少 `uuid/uuid.h` 失败；保留摘要和日志。补入 `uuid-dev 2.39.3-9ubuntu6` 后使用新的 `c-native-xrtsim-v2` 构建目录。私有 g++ 启动脚本仅增加该头文件目录，真实编译器仍为 `/usr/bin/g++`，启动脚本与编译器哈希均记录；没有修改固定源码或压掉诊断。

## 在原环境复跑

先按固定版本准备工具链、Ramulator 依赖和宿主依赖。使用 `run_native_smoke.py --backend rtlsim|xrtsim --target-profile block32-v1 --jobs 2`，指定新的构建目录、run_id 和结果目录。原生示例通过后再创建对应绑定：

```bash
python3 -B scripts/bind_simx_runtime.py \
  --summary "$NATIVE_SUMMARY" \
  --target-lock configs/candidates/block32-v1/target_lock.json \
  --hardware configs/candidates/block32-v1/native_smoke.json \
  --output "$NEW_BINDING"
```

脚本名称沿用早期入口，但 v3 支持三种仿真后端。设置 `LD_LIBRARY_PATH` 为该构建的 `sw/runtime`，不要混入其他构建；处理器 RTL 设置 `VORTEX_DRIVER=rtlsim`，AFU 模型设置 `VORTEX_DRIVER=xrt`。每个绑定/模块用独立进程：

```bash
python3 -B scripts/run_ptx_suite.py --backend xrtsim --kernel affine \
  --module "$MODULE" --binding "$NEW_BINDING/binding.json" \
  --target-lock configs/candidates/block32-v1/target_lock.json \
  --output "$NEW_RESULT"
```

`MODULE` 使用与候选 lock 匹配、已通过固定工具链编译的模块；不能把基线 16 线程模块、U280 配置或其他运行库混用。本轮复用上一批三个 block32 模块的原始字节。所有变量表示本机实际路径，完整实跑命令保存在 suite/native 摘要中。

## 当前服务器实查

本次以本人账户只读检查 `~/gpgpu_work` 和可见 U280 sysfs，记录时间为 2026-11-11 08:41（北京时间）：

- 该项目目录没有 `.xclbin`、`libvortex.so` 或 `libvortex-xrt.so`。这不表示其他同学账户里没有产物。
- 8 张卡均报告 ready；7 张 `host_mem_size=268435456`，`0000:b5:00.1` 为 0。不能再把旧报告中的“8 张全部 HOST=0”当作当前阻塞。
- 本账户对 8 个 render 节点均有读写权限；KDS 当次未显示在途任务和 client pid。部分卡已有 xclbin UUID；这些快照不构成分卡预留，也没有证明所有用户的文件占用均已排除。
- glibc 2.17、GCC 9.3.1、XRT/XOCL/XCLMGMT 2.13.479 查询退出 0。
- 没有执行 sudo、HOST 配置、设备打开、加载、reset 或 kernel。

## 需要同学提供的具体内容

| 接口 / 同学 | 需要交付 | C 收到后继续做什么 |
|---|---|---|
| A/B：实际 U280 目标 | 当前采用的 `target_lock.json`、caps、RTL 配置/补丁和提交；确认是否采用 8w×4t、200 MHz、HBM32 候选 | 按真实目标生成独立板上模块与运行库绑定；不把仿真 lock 当作板上 lock |
| B：FPGA 产物与平台 | 本账户可读取的 `.xclbin` 路径、SHA-256、对应平台/shell、完整构建和时序报告；对 TIMING-7/跨域约束问题的关闭或工程审阅结论；匹配的 Runtime 源码/补丁与构建配置 | 复核产物、在当前服务器编译/校验 Runtime，核对实际加载 UUID/时钟，接通三类 PTX；现有公开快照未包含完整 FPGA 包，不能靠示例路径猜测 |
| B / 资源负责人：用卡安排 | 可使用的卡 BDF 和时间段，按团队规则确认占用；必要时由有权限者检查所有用户占用 | 在已配置 HOST 的卡上受控执行原生程序，再做 PTX、数据搬运、完成和故障处理验证 |
| E：独立接收 | 独立生成输入和答案的代码/版本、冻结用例与边界、验收命令、非作者运行记录 | 配合修复接收问题，归档独立结果；不能用本人的核对器代替 E 的独立 oracle |
| D / 团队：接口接收 | 确认采用当前前端 v1.2、模块/参数 ABI 与 PTX P0 白名单，给出团队合入目标分支 | 提交 C 的改动并解决实际接口差异；个人仓库上传不等于团队合并 |

板上实际完成语义、PCIe/DMA 故障隔离、硬复位与硬件性能仍未验证。本轮超时处理只承诺等待在途任务排空后重建资源；没有证明安全 abort。三类整数样例也不构成完整 PTX/CUDA 指令、任意程序或模型兼容声明。
