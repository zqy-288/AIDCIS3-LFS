import ctypes
import time
import csv
import os
from datetime import datetime

# 精确匹配SDK的C语言类型定义
TSCMCAPI_InstanceHandle = ctypes.c_uint64  # SDK中对应uint64_t，64位无符号整数
uint8_t = ctypes.c_ubyte
uint32_t = ctypes.c_uint32
int32_t = ctypes.c_int32
bool = ctypes.c_bool


# 结构体定义与SDK严格一致
class IPAddr(ctypes.Structure):
    _fields_ = [("c1", uint8_t),
                ("c2", uint8_t),
                ("c3", uint8_t),
                ("c4", uint8_t)]


class DataCfg(ctypes.Structure):
    _fields_ = [("channel", int32_t),
                ("type", int32_t)]


class DataNode(ctypes.Structure):
    _fields_ = [("cfg", DataCfg),
                ("data", ctypes.c_double)]


# 错误码定义
TS_ERRCODE_OK = 0
TS_ERRCODE_DEVICE_NOT_CONNECTED = -12
TS_ERRCODE_INVALID_PARAMETER = -8
TS_ERRCODE_TIMEOUT = -2

# 控制器配置
CONTROLLERS = [
    {
        "name": "控制器1",
        "ip": "192.168.0.10",
        "controller_port": 8000,
        "local_port": 8001,
        "channels": [1, 2]
    },
    {
        "name": "控制器2",
        "ip": "192.168.0.11",
        "controller_port": 8000,
        "local_port": 8002,
        "channels": [1]
    }
]

# 采集参数
RECORD_DURATION = 30  # 数据记录时长（秒）


def load_dll():
    """加载动态链接库并配置函数接口"""
    try:
        dll_path = r'TSCMCCommon/clib/Release/x64/TSCMCAPIC.dll'
        protocol = ctypes.CDLL(dll_path)
        print(f"DLL加载成功: {dll_path}")

        # 配置函数接口
        protocol.TSCMCAPI_CreateInstance.restype = TSCMCAPI_InstanceHandle
        protocol.TSCMCAPI_CreateInstance.argtypes = []

        protocol.TSCMCAPI_ReleaseInstance.argtypes = [TSCMCAPI_InstanceHandle]
        protocol.TSCMCAPI_ReleaseInstance.restype = None

        protocol.TSCMCAPI_SetConnectionType.argtypes = [TSCMCAPI_InstanceHandle, int32_t]
        protocol.TSCMCAPI_SetConnectionType.restype = bool

        protocol.TSCMCAPI_SetUdpPort.argtypes = [TSCMCAPI_InstanceHandle, int32_t]
        protocol.TSCMCAPI_SetUdpPort.restype = bool

        protocol.TSCMCAPI_SetDestUdpEndPoint.argtypes = [TSCMCAPI_InstanceHandle, ctypes.c_char_p, int32_t]
        protocol.TSCMCAPI_SetDestUdpEndPoint.restype = bool

        protocol.TSCMCAPI_OpenConnectionPort.argtypes = [TSCMCAPI_InstanceHandle]
        protocol.TSCMCAPI_OpenConnectionPort.restype = bool

        protocol.TSCMCAPI_CloseConnectionPort.argtypes = [TSCMCAPI_InstanceHandle]
        protocol.TSCMCAPI_CloseConnectionPort.restype = None

        protocol.TSCMCAPI_SetConnectionOn.argtypes = [TSCMCAPI_InstanceHandle, int32_t]
        protocol.TSCMCAPI_SetConnectionOn.restype = int32_t

        protocol.TSCMCAPI_SetConnectionOff.argtypes = [TSCMCAPI_InstanceHandle, int32_t]
        protocol.TSCMCAPI_SetConnectionOff.restype = int32_t

        protocol.TSCMCAPI_isConnected.argtypes = [TSCMCAPI_InstanceHandle, int32_t]
        protocol.TSCMCAPI_isConnected.restype = bool

        protocol.TSCMCAPI_GetSingleDataNode.argtypes = [
            TSCMCAPI_InstanceHandle, int32_t,
            ctypes.POINTER(DataNode),
            ctypes.POINTER(int32_t), int32_t]
        protocol.TSCMCAPI_GetSingleDataNode.restype = int32_t

        protocol.TSCMCAPI_SetConfigOutputSignals.argtypes = [
            TSCMCAPI_InstanceHandle, int32_t, int32_t, int32_t,
            ctypes.POINTER(int32_t), int32_t]
        protocol.TSCMCAPI_SetConfigOutputSignals.restype = int32_t

        return protocol
    except Exception as e:
        print(f"DLL加载失败: {str(e)}")
        return None


def check_connection_status(protocol, instance, controller_name):
    """检查控制器连接状态"""
    try:
        if not protocol.TSCMCAPI_isConnected(instance, 0):
            print(f"[{controller_name}] 连接已断开")
            return False
        return True
    except Exception as e:
        print(f"[{controller_name}] 连接状态检查异常: {str(e)}")
        return False


def disconnect_controller(protocol, instance, controller_name):
    """安全断开控制器连接"""
    try:
        protocol.TSCMCAPI_SetConnectionOff(instance, 0)
        protocol.TSCMCAPI_CloseConnectionPort(instance)
        protocol.TSCMCAPI_ReleaseInstance(instance)
        print(f"[{controller_name}] 连接已安全断开")
        return True
    except Exception as e:
        print(f"[{controller_name}] 断开连接时异常: {str(e)}")
        return False


def connect_to_controller(protocol, controller_config, max_retries=3, retry_delay=2):
    """连接到指定控制器（带重试机制）"""
    name = controller_config["name"]
    ip = controller_config["ip"]
    controller_port = controller_config["controller_port"]
    local_port = controller_config["local_port"]

    for attempt in range(max_retries):
        print(f"\n=== 开始连接{name} ({ip}:{controller_port}) - 尝试 {attempt + 1}/{max_retries} ===")

        instance = protocol.TSCMCAPI_CreateInstance()
        if not instance:
            print(f"[{name}] 实例创建失败，可能为DLL与Python架构不匹配")
            if attempt < max_retries - 1:
                print(f"[{name}] {retry_delay}秒后重试...")
                time.sleep(retry_delay)
                continue
            return None

        try:
            # 设置通信类型为以太网
            if not protocol.TSCMCAPI_SetConnectionType(instance, 2):
                print(f"[{name}] 设置通信类型失败")
                protocol.TSCMCAPI_ReleaseInstance(instance)
                if attempt < max_retries - 1:
                    print(f"[{name}] {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                return None

            # 设置本地监听端口
            if not protocol.TSCMCAPI_SetUdpPort(instance, local_port):
                print(f"[{name}] 设置本地端口失败")
                protocol.TSCMCAPI_ReleaseInstance(instance)
                if attempt < max_retries - 1:
                    print(f"[{name}] {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                return None

            # 设置控制器IP和端口
            dest_addr = ip.encode('utf-8')
            if not protocol.TSCMCAPI_SetDestUdpEndPoint(instance, dest_addr, controller_port):
                print(f"[{name}] 设置控制器IP失败")
                protocol.TSCMCAPI_ReleaseInstance(instance)
                if attempt < max_retries - 1:
                    print(f"[{name}] {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                return None

            # 打开连接通道
            if not protocol.TSCMCAPI_OpenConnectionPort(instance):
                err = ctypes.get_last_error()
                print(f"[{name}] 打开通道失败，系统错误码: {err}")
                protocol.TSCMCAPI_ReleaseInstance(instance)
                if attempt < max_retries - 1:
                    print(f"[{name}] {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                return None

            # 连接确认
            err = protocol.TSCMCAPI_SetConnectionOn(instance, 0)
            if err != TS_ERRCODE_OK:
                print(f"[{name}] 连接确认失败，错误码: {err}")
                protocol.TSCMCAPI_ReleaseInstance(instance)
                if attempt < max_retries - 1:
                    print(f"[{name}] {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                return None

            # 检查连接状态
            if not protocol.TSCMCAPI_isConnected(instance, 0):
                print(f"[{name}] 连接状态检查失败")
                protocol.TSCMCAPI_ReleaseInstance(instance)
                if attempt < max_retries - 1:
                    print(f"[{name}] {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                return None

            print(f"[{name}] 已成功连接")
            return instance

        except Exception as e:
            print(f"[{name}] 连接异常: {str(e)}")
            try:
                protocol.TSCMCAPI_ReleaseInstance(instance)
            except:
                pass
            if attempt < max_retries - 1:
                print(f"[{name}] {retry_delay}秒后重试...")
                time.sleep(retry_delay)
                continue
            return None

    print(f"[{name}] 所有重试尝试失败，连接失败")
    return None


def configure_data_output(protocol, instance, controller_config):
    """配置控制器输出多通道距离数据"""
    name = controller_config["name"]
    channels = controller_config["channels"]

    print(f"[{name}] 配置多通道数据输出类型为距离")

    # 为每个通道配置输出类型为距离1
    for channel in channels:
        data_types = (int32_t * 1)()
        data_types[0] = 1  # 距离1

        err = protocol.TSCMCAPI_SetConfigOutputSignals(
            instance, 0, channel, 2, data_types, 1)

        if err != TS_ERRCODE_OK:
            print(f"[{name}] 配置通道{channel}输出数据类型失败，错误码: {err}")
            return False

        print(f"[{name}] 通道{channel}配置为输出距离数据")

    return True


def read_channel_data(protocol, instance, controller_name, channel):
    """读取指定控制器指定通道的距离数据"""
    data_nodes = (DataNode * 10)()
    nread = int32_t(0)
    err = protocol.TSCMCAPI_GetSingleDataNode(
        instance, 0, data_nodes, ctypes.byref(nread), 10)

    if err == TS_ERRCODE_OK and nread.value > 0:
        # 遍历数据节点，查找指定通道的数据
        for i in range(nread.value):
            if data_nodes[i].cfg.channel == channel:
                return data_nodes[i].data
        print(f"[{controller_name}] 未找到通道{channel}的数据")
    else:
        print(f"[{controller_name}] 读取通道{channel}数据失败，错误码: {err}")

    return None


def save_data_to_csv(data_list, filename):
    """将多控制器多通道数据保存到CSV文件"""
    if not data_list:
        print("[警告] 没有数据可保存")
        return

    # 动态生成CSV表头（基于所有数据点的键）
    fieldnames = set()
    for data_point in data_list:
        fieldnames.update(data_point.keys())
    fieldnames = sorted(fieldnames)

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for data_point in data_list:
            writer.writerow(data_point)

    print(f"数据已成功保存到 {filename}")


# 简单的callback函数示例，用于打印采集到的数据
def simple_callback(data_str, distance, controller_name, channel):
    print(f"采集到 {controller_name} 通道 {channel} 的数据: {distance:.4f} mm")


class Acquisition:
    def __init__(self, protocol, callback, sampling_interval=0.5):
        self.protocol = protocol
        self.callback = callback
        self.controller_instances = {}
        self.running = False
        self.data_list = []
        self.sampling_interval = sampling_interval  # 存储采样间隔

        # 连接监控参数
        self.connection_check_interval = 10  # 每10秒检查一次连接状态
        self.last_connection_check = 0
        self.auto_reconnect = True  # 是否启用自动重连
        self.max_reconnect_attempts = 3  # 最大重连尝试次数
        self.reconnect_delay = 5  # 重连延迟（秒）
        self.failed_controllers = set()  # 记录连接失败的控制器

    def start(self):
        if self.running:
            return
        self.running = True

        # 连接所有控制器
        self.controller_instances = {}
        for config in CONTROLLERS:
            instance = connect_to_controller(self.protocol, config)
            if instance:
                self.controller_instances[config["name"]] = {
                    "instance": instance,
                    "config": config
                }

        # 检查是否成功连接至少一个控制器
        if not self.controller_instances:
            print("[错误] 所有控制器连接失败，程序退出")
            self.running = False
            return

        # 配置所有控制器的数据输出
        for name, controller in self.controller_instances.items():
            if not configure_data_output(self.protocol, controller["instance"], controller["config"]):
                print(f"[{name}] 数据输出配置失败，将跳过该控制器")
                del self.controller_instances[name]

        # 再次检查是否还有可用的控制器
        if not self.controller_instances:
            print("[错误] 所有控制器配置失败，程序退出")
            self.running = False
            return

        try:
            end_time = time.time() + RECORD_DURATION

            print("[开始] 多控制器多通道数据采集...")
            while self.running and time.time() < end_time:
                # 初始化当前时间点的数据
                current_data = {'时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]}
                measure_list = []

                # 遍历每个控制器
                for name, controller in self.controller_instances.items():
                    instance = controller["instance"]
                    channels = controller["config"]["channels"]

                    # 逐个通道读取数据
                    for channel in channels:
                        distance = read_channel_data(self.protocol, instance, name, channel)
                        key = f"{name}通道{channel}距离(mm)"

                        if distance is not None:
                            current_data[key] = distance
                            data_str = f"{current_data['时间']}, 端口: {controller['config']['controller_port']}, 通道: {channel}, 距离: {distance:.4f} mm"
                            self.callback(data_str, distance, name, channel)
                            if name == "控制器1":
                                if channel == 1:
                                    measure_list.append(distance)
                                elif channel == 2:
                                    measure_list.append(distance)
                            elif name == "控制器2" and channel == 1:
                                measure_list.append(distance)
                        else:
                            current_data[key] = "N/A"
                            print(f"[{name}] 通道{channel}数据读取失败")

                # 添加数据点到列表
                self.data_list.append(current_data)

                # 等待采样间隔
                time.sleep(self.sampling_interval)

        except OverflowError as oe:
            print(f"[严重错误] 内存溢出，错误: {str(oe)}")
            print("[解决方案] 确认所有ctypes类型与SDK完全一致，尤其是64位整数")
        except KeyboardInterrupt:
            print("\n[用户中断] 停止数据采集")
        except Exception as e:
            print(f"[运行异常] {str(e)}")

    def stop(self):
        if not self.running:
            return
        self.running = False
        # 释放所有控制器资源
        print("\n[步骤] 断开所有连接并释放资源")
        for name, controller in self.controller_instances.items():
            try:
                self.protocol.TSCMCAPI_SetConnectionOff(controller["instance"], 0)
                self.protocol.TSCMCAPI_CloseConnectionPort(controller["instance"])
                self.protocol.TSCMCAPI_ReleaseInstance(controller["instance"])
                print(f"[{name}] 资源释放成功")
            except Exception as e:
                print(f"[{name}] 资源释放异常: {str(e)}")

        print("[完成] 所有资源释放成功")
        print("=== 程序执行完毕 ===")

    def check_and_reconnect_controllers(self):
        """检查控制器连接状态并尝试重连"""
        current_time = time.time()

        # 检查是否到了连接检查时间
        if current_time - self.last_connection_check < self.connection_check_interval:
            return

        self.last_connection_check = current_time
        print("\n[连接监控] 开始检查控制器连接状态...")

        disconnected_controllers = []

        # 检查每个控制器的连接状态
        for name, controller in list(self.controller_instances.items()):
            instance = controller["instance"]

            if not check_connection_status(self.protocol, instance, name):
                print(f"[连接监控] {name} 连接已断开")
                disconnected_controllers.append((name, controller))

                # 清理断开的连接
                try:
                    disconnect_controller(self.protocol, instance, name)
                except:
                    pass

                # 从活动控制器列表中移除
                del self.controller_instances[name]

        # 尝试重连断开的控制器
        if disconnected_controllers and self.auto_reconnect:
            self.reconnect_controllers(disconnected_controllers)

    def reconnect_controllers(self, disconnected_controllers):
        """重连断开的控制器"""
        print(f"[自动重连] 尝试重连 {len(disconnected_controllers)} 个控制器...")

        for name, controller in disconnected_controllers:
            config = controller["config"]

            # 检查是否已经尝试过重连
            if name in self.failed_controllers:
                continue

            print(f"[自动重连] 正在重连 {name}...")

            # 尝试重新连接
            new_instance = connect_to_controller(
                self.protocol,
                config,
                max_retries=self.max_reconnect_attempts,
                retry_delay=self.reconnect_delay
            )

            if new_instance:
                # 重新配置数据输出
                if configure_data_output(self.protocol, new_instance, config):
                    # 重连成功，添加回控制器列表
                    self.controller_instances[name] = {
                        "instance": new_instance,
                        "config": config
                    }
                    print(f"[自动重连] {name} 重连成功")

                    # 从失败列表中移除（如果存在）
                    self.failed_controllers.discard(name)
                else:
                    print(f"[自动重连] {name} 重连后配置失败")
                    disconnect_controller(self.protocol, new_instance, name)
                    self.failed_controllers.add(name)
            else:
                print(f"[自动重连] {name} 重连失败")
                self.failed_controllers.add(name)

    def get_connection_status(self):
        """获取当前连接状态信息"""
        total_controllers = len(CONTROLLERS)
        connected_controllers = len(self.controller_instances)
        failed_controllers = len(self.failed_controllers)

        status = {
            'total': total_controllers,
            'connected': connected_controllers,
            'failed': failed_controllers,
            'connection_rate': connected_controllers / total_controllers if total_controllers > 0 else 0,
            'controller_details': {}
        }

        # 添加每个控制器的详细状态
        for config in CONTROLLERS:
            name = config["name"]
            if name in self.controller_instances:
                status['controller_details'][name] = 'connected'
            elif name in self.failed_controllers:
                status['controller_details'][name] = 'failed'
            else:
                status['controller_details'][name] = 'unknown'

        return status

    def get_data_list(self):
        return self.data_list


if __name__ == "__main__":
    protocol = load_dll()
    if protocol:
        acquisition = Acquisition(protocol, simple_callback)
        acquisition.start()