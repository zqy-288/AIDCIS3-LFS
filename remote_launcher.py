import subprocess
import os

# --- 1. 配置区域 ---
# (这部分保持不变)
PSEXEC_PATH = r"D:\PSTools\PsExec64.exe" 
REMOTE_PC_IP = "192.168.0.101"
REMOTE_USERNAME = "WIN10"
REMOTE_PASSWORD = "123456"
EXE_ON_REMOTE = r"D:\gugao\GEN\my_Ecat_Init\Debug\Ecat_Init.exe" 


def start_remote_exe_with_psexec():
    """
    使用 PsExec 远程启动目标电脑上的 .exe 文件。
    """
    print("--- 远程执行任务开始 ---")

    if not os.path.exists(PSEXEC_PATH):
        print(f"[错误] PsExec 工具未在指定路径找到: {PSEXEC_PATH}")
        return False

    command = [
        PSEXEC_PATH,
        f'\\\\{REMOTE_PC_IP}',
        '-u', REMOTE_USERNAME,
        '-p', REMOTE_PASSWORD,
        '-accepteula',
        '-d',  
        '-i',  
        EXE_ON_REMOTE
    ]
    
    print(f"准备执行命令: {' '.join(command)}")

    try:
        # --- 核心修改：移除 check=True ---
        # 我们将手动检查返回结果，不再让它自动抛出异常。
        result = subprocess.run(command, capture_output=True)

        # PsExec 成功启动远程进程后，返回码是远程进程的ID（大于0）
        # 如果连接失败（如密码错误），返回码通常是-1或其他非零值，但标准错误流(stderr)会有明确的错误文本。
        
        # 安全地解码 stderr，检查是否有错误信息
        stderr_msg = ""
        if result.stderr:
            try:
                stderr_msg = result.stderr.decode('gbk')
            except:
                stderr_msg = result.stderr.decode('utf-8', errors='ignore')

        # 判断是否真正成功：stderr中包含 "started on" 并且返回码大于0
        if result.returncode > 0 and "started on" in stderr_msg:
            print(f"[成功] 远程程序已在 {REMOTE_PC_IP} 上启动！")
            print(f"远程进程ID (PID): {result.returncode}")
            print(f"PsExec输出: {stderr_msg.strip()}")
            return True
        else:
            # 如果不是预期的成功，则打印所有信息以供调试
            print("[错误] PsExec 执行失败或返回了意外的结果。")
            print(f"返回码: {result.returncode}")
            
            stdout_msg = result.stdout.decode('gbk', errors='ignore') if result.stdout else "（无）"
            
            print("--- 标准输出 (stdout) ---")
            print(stdout_msg)
            print("--------------------------")
            print("--- 标准错误 (stderr) ---")
            print(stderr_msg if stderr_msg else "（无）")
            print("--------------------------")
            return False

    except Exception as e:
        print(f"[致命错误] 执行过程中发生未知异常: {e}")
        return False

# --- 程序主入口 ---
if __name__ == '__main__':
    start_remote_exe_with_psexec()