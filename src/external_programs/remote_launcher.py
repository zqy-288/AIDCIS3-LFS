import subprocess
import os
import time
import re

# --- 1. 配置区域 ---
PSEXEC_PATH = r"F:\PSTools\PsExec64.exe" 
REMOTE_PC_IP = "192.168.0.101"
REMOTE_USERNAME = "WIN10"
REMOTE_PASSWORD = "123456"
# PC B上被控程序exe的完整路径
EXE_ON_REMOTE = r"D:\gugao\GEN\my_Ecat_Init\Debug\Ecat_Init.exe" 

# --- 2. 自动化流程相关配置 ---
# PC B上共享文件夹中的标志文件的网络访问路径(UNC路径)
# 请确保PC B上的 'gugao' 文件夹已设置为共享，且WIN10用户有读写权限
FLAG_FILE_UNC_PATH = f"\\\\{REMOTE_PC_IP}\\gugao\\task_complete.flag" 

# 等待标志文件的超时时间（秒）
WAIT_TIMEOUT_SECONDS = 300 # 5分钟

# 检查标志文件的时间间隔（秒）
POLL_INTERVAL_SECONDS = 2

# 用于在本地保存远程进程PID的文件名
PID_FILE = "remote_pid.txt"


def get_active_session_id():
    """获取远程计算机的活动会话ID"""
    print("正在获取远程计算机的活动会话ID...")
    command = [PSEXEC_PATH, f'\\\\{REMOTE_PC_IP}', '-u', REMOTE_USERNAME, '-p', REMOTE_PASSWORD, '-accepteula', 'query', 'session']
    result = subprocess.run(command, capture_output=True)
    
    output = result.stdout.decode('gbk', errors='ignore') if result.stdout else ""
    error = result.stderr.decode('gbk', errors='ignore') if result.stderr else ""
    
    # 检查输出中是否包含活动会话信息
    # 典型输出格式: "RDP-Tcp#0    Active          1  user"
    match = re.search(r'(\w+)\s+Active\s+(\d+)', output)
    if match:
        session_id = match.group(2)
        print(f"找到活动会话ID: {session_id}")
        return session_id
    else:
        print(f"未找到活动会话，使用默认会话ID 1。输出信息: {output}")
        return "1"


def start_remote_exe():
    """远程启动程序，并将其PID保存到文件中。"""
    print("--- 远程启动任务开始 ---")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE) # 每次启动前清理旧的PID文件
        
    if not os.path.exists(PSEXEC_PATH):
        print(f"[错误] PsExec 工具未在指定路径找到: {PSEXEC_PATH}")
        return None
    
    # 获取活动会话ID
    session_id = get_active_session_id()
        
    # 修改命令，指定会话ID并使用分离模式
    command = [
        PSEXEC_PATH, 
        f'\\\\{REMOTE_PC_IP}', 
        '-u', REMOTE_USERNAME, 
        '-p', REMOTE_PASSWORD, 
        '-accepteula', 
        '-i', session_id,  # 指定活动会话ID
        '-d',              # 使用分离模式，不等待程序终止
        EXE_ON_REMOTE
    ]
    
    print(f"准备执行启动命令: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True)
    
    stderr_msg = result.stderr.decode('gbk', errors='ignore') if result.stderr else ""
    
    if result.returncode > 0 and "started on" in stderr_msg:
        pid = result.returncode
        print(f"[成功] 远程程序已启动！PID: {pid}")
        with open(PID_FILE, "w") as f:
            f.write(str(pid))
        return pid
    else:
        print("[错误] 远程程序启动失败。")
        stdout_msg = result.stdout.decode('gbk', errors='ignore') if result.stdout else "（无）"
        print(f"返回码: {result.returncode}\n--- stdout ---\n{stdout_msg}\n--- stderr ---\n{stderr_msg}")
        return None

def stop_remote_exe(pid):
    """使用PID远程停止程序。"""
    print(f"--- 远程停止任务开始 (PID: {pid}) ---")
    if not str(pid).isdigit():
        print(f"[错误] 无效的PID: {pid}")
        return False
        
    command = [ 
        PSEXEC_PATH, 
        f'\\\\{REMOTE_PC_IP}', 
        '-u', REMOTE_USERNAME, 
        '-p', REMOTE_PASSWORD, 
        '-accepteula', 
        '-i', "1",  # 停止命令可能不需要指定特定会话
        "taskkill", "/PID", str(pid), "/F"
    ]
    print(f"准备执行停止命令: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True)
    
    stdout_msg = result.stdout.decode('gbk', errors='ignore') if result.stdout else ""
    stderr_msg = result.stderr.decode('gbk', errors='ignore') if result.stderr else ""
    
    if result.returncode == 0 and ("成功" in stdout_msg or "SUCCESS" in stdout_msg):
        print(f"[成功] 远程进程 (PID: {pid}) 已被终止。")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return True
    elif "not found" in stderr_msg:
        print(f"[信息] 远程进程 (PID: {pid}) 未找到，可能已关闭。")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return True
    else:
        print("[错误] 发送停止命令失败。")
        print(f"返回码: {result.returncode}")
        print(f"--- 标准输出 ---\n{stdout_msg}\n--------------------")
        print(f"--- 标准错误 ---\n{stderr_msg}\n--------------------")
        return False

# --- 程序主入口：完整的自动化流程 ---
if __name__ == '__main__':
    # 第1步：启动远程程序
    remote_pid = start_remote_exe()

    if remote_pid:
        # 第2步：等待任务完成的标志文件
        print(f"\n程序已启动，现在开始等待任务完成标志文件...")
        print(f"将每隔 {POLL_INTERVAL_SECONDS} 秒检查一次路径: {FLAG_FILE_UNC_PATH}")
        
        start_time = time.time()
        task_completed = False
        
        while time.time() - start_time < WAIT_TIMEOUT_SECONDS:
            if os.path.exists(FLAG_FILE_UNC_PATH):
                print(f"\n[检测到标志文件] 远程任务已完成！")
                task_completed = True
                try:
                    os.remove(FLAG_FILE_UNC_PATH)
                    print("标志文件已成功删除。")
                except OSError as e:
                    print(f"[警告] 删除标志文件失败: {e}")
                break
            
            elapsed_time = int(time.time() - start_time)
            print(f"已等待 {elapsed_time} 秒...", end='\r')
            time.sleep(POLL_INTERVAL_SECONDS)

        if not task_completed:
            print(f"\n[超时错误] 等待超过 {WAIT_TIMEOUT_SECONDS} 秒，未检测到任务完成标志文件。")

        # 第3步：无论任务是否完成或超时，都尝试停止远程进程
        print("\n准备执行清理和停止程序...")
        stop_remote_exe(remote_pid)
        
    print("\n--- 自动化流程结束 ---")


class RemoteLauncher:
    """远程启动器类，用于管理远程程序的启动和停止"""

    def __init__(self):
        self.remote_pid = None

    def start_remote_program(self):
        """启动远程程序"""
        try:
            self.remote_pid = start_remote_exe()
            return self.remote_pid is not None
        except Exception as e:
            print(f"启动远程程序失败: {e}")
            return False

    def stop_remote_program(self):
        """停止远程程序"""
        try:
            if self.remote_pid:
                stop_remote_exe(self.remote_pid)
                self.remote_pid = None
                return True
            return False
        except Exception as e:
            print(f"停止远程程序失败: {e}")
            return False

    def run_automation_workflow(self):
        """运行完整的自动化工作流程"""
        try:
            automation_workflow()
            return True
        except Exception as e:
            print(f"自动化工作流程失败: {e}")
            return False