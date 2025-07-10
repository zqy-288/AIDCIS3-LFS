#!/usr/bin/env python3
"""
GitHub上传助手
帮助用户完成项目上传到GitHub的全过程
"""

import subprocess
import sys
import webbrowser
from pathlib import Path

def run_command(command, capture_output=True):
    """运行命令并返回结果"""
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(command, shell=True)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def check_git_status():
    """检查Git状态"""
    print("🔍 检查当前Git状态...")
    
    # 检查是否在Git仓库中
    success, output, error = run_command("git status")
    if not success:
        print("❌ 当前目录不是Git仓库")
        return False
    
    # 检查是否有未提交的更改
    success, output, error = run_command("git status --porcelain")
    if output.strip():
        print("⚠️ 有未提交的更改，正在提交...")
        run_command("git add .")
        run_command('git commit -m "Final commit before GitHub upload"')
    
    # 检查远程仓库
    success, output, error = run_command("git remote -v")
    if output.strip():
        print("✅ 远程仓库已配置:")
        print(output)
        return True
    else:
        print("⚠️ 未配置远程仓库")
        return False

def open_github():
    """打开GitHub创建仓库页面"""
    print("\n🌐 正在打开GitHub创建仓库页面...")
    webbrowser.open("https://github.com/new")
    print("✅ 已在浏览器中打开GitHub")

def setup_remote_repo():
    """设置远程仓库"""
    print("\n📋 GitHub仓库创建指南:")
    print("1. 仓库名称: AIDCIS2-AIDCIS3")
    print("2. 描述: 管孔检测系统上位机软件")
    print("3. 选择 Public 或 Private")
    print("4. ⚠️ 不要勾选 'Add a README file'")
    print("5. ⚠️ 不要勾选 'Add .gitignore'")
    print("6. 点击 'Create repository'")
    
    input("\n按Enter键继续，当您完成GitHub仓库创建后...")
    
    print("\n📝 请输入您的GitHub仓库URL:")
    print("格式: https://github.com/YOUR-USERNAME/AIDCIS2-AIDCIS3.git")
    
    while True:
        repo_url = input("仓库URL: ").strip()
        if repo_url and "github.com" in repo_url and repo_url.endswith(".git"):
            break
        print("❌ 请输入有效的GitHub仓库URL")
    
    # 添加远程仓库
    print(f"\n🔗 正在添加远程仓库: {repo_url}")
    success, output, error = run_command(f"git remote add origin {repo_url}")
    
    if not success and "already exists" in error:
        print("⚠️ 远程仓库已存在，正在更新...")
        success, output, error = run_command(f"git remote set-url origin {repo_url}")
    
    if success:
        print("✅ 远程仓库配置成功")
        return repo_url
    else:
        print(f"❌ 配置失败: {error}")
        return None

def push_to_github(repo_url):
    """推送到GitHub"""
    print(f"\n🚀 正在推送到GitHub...")
    print("这可能需要几分钟时间，因为包含Git LFS文件...")
    
    # 显示LFS文件信息
    success, output, error = run_command("git lfs ls-files")
    if success and output:
        lfs_files = output.split('\n')
        print(f"📦 将上传 {len(lfs_files)} 个LFS文件")
    
    # 推送到GitHub
    success, output, error = run_command("git push -u origin main", capture_output=False)
    
    if success:
        print("\n🎉 成功推送到GitHub!")
        print(f"📍 您的仓库地址: {repo_url.replace('.git', '')}")
        return True
    else:
        print(f"\n❌ 推送失败")
        print("可能的原因:")
        print("1. 认证问题 - 需要GitHub用户名和密码/Token")
        print("2. 网络问题 - 检查网络连接")
        print("3. 权限问题 - 确保有仓库写入权限")
        print("4. LFS配额问题 - 检查GitHub LFS使用量")
        return False

def show_team_instructions(repo_url):
    """显示团队协作说明"""
    print("\n👥 团队成员协作指南:")
    print("=" * 50)
    print(f"1. 克隆仓库:")
    print(f"   git clone {repo_url}")
    print()
    print("2. 安装Git LFS:")
    print("   访问 https://git-lfs.github.io/ 下载安装")
    print()
    print("3. 拉取LFS文件:")
    print("   git lfs pull")
    print()
    print("4. 安装依赖:")
    print("   pip install -r requirements.txt")
    print()
    print("5. 运行程序:")
    print("   python src/main.py")
    print("=" * 50)

def main():
    """主函数"""
    print("🚀 GitHub上传助手")
    print("=" * 50)
    print("这个助手将帮助您将AIDCIS2-AIDCIS3项目上传到GitHub")
    print()
    
    # 检查Git状态
    has_remote = check_git_status()
    
    if not has_remote:
        # 打开GitHub创建仓库页面
        open_github()
        
        # 设置远程仓库
        repo_url = setup_remote_repo()
        if not repo_url:
            print("❌ 远程仓库设置失败，请手动配置")
            return
    else:
        # 获取现有远程仓库URL
        success, output, error = run_command("git remote get-url origin")
        repo_url = output.strip() if success else None
    
    if repo_url:
        # 推送到GitHub
        if push_to_github(repo_url):
            # 显示团队协作说明
            show_team_instructions(repo_url)
            
            print("\n✅ 上传完成!")
            print("您的项目现在可以在GitHub上访问了!")
        else:
            print("\n🔧 推送失败，您可以稍后手动推送:")
            print("git push origin main")
    
    input("\n按Enter键退出...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        input("按Enter键退出...")
