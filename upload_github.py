"""
GitHub 一键上传脚本
==================
放在项目根目录（与 README.md、requirements.txt 同级）。

使用方法：
1. 保存本文件为 upload_github.py
2. 在 VS Code 终端进入项目根目录
3. 执行：python upload_github.py
4. 输入本次修改说明，脚本会自动执行 git add、git commit、git push

注意：
- 脚本会提交当前项目中所有未被 .gitignore 排除的改动。
- 如果没有改动，会提示并退出。
- 如果 push 失败，请检查网络、GitHub 认证及代理设置。
"""

import subprocess
import sys


def run_git(args, check=True):
    """执行 Git 命令，并显示输出。"""
    command = ["git"] + args
    result = subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if check and result.returncode != 0:
        raise RuntimeError(f"Git 命令执行失败：git {' '.join(args)}")

    return result


def main():
    print("=" * 50)
    print("          GitHub 一键上传工具")
    print("=" * 50)

    # 检查是否处于 Git 仓库中
    check_repo = run_git(
        ["rev-parse", "--is-inside-work-tree"],
        check=False,
    )
    if check_repo.returncode != 0:
        print("错误：当前目录不是 Git 仓库。")
        print("请先在 VS Code 终端进入项目根目录，再运行本脚本。")
        return 1

    # 显示当前分支
    branch_result = run_git(["branch", "--show-current"])
    branch = branch_result.stdout.strip() if branch_result.stdout else "未知"
    print(f"当前分支：{branch}")

    # 检查是否有文件改动
    status = run_git(["status", "--short"])
    if not status.stdout.strip():
        print("\n当前没有需要上传的文件，已退出。")
        return 0

    print("\n本次待提交的文件：")
    print(status.stdout)

    message = input("请输入本次修改说明（例如：更换腾讯行情数据接口）：").strip()
    if not message:
        print("修改说明不能为空，已退出。")
        return 1

    confirm = input("\n确认提交并上传到 GitHub？(y/n)：").strip().lower()
    if confirm not in ("y", "yes"):
        print("已取消，没有执行上传。")
        return 0

    try:
        print("\n[1/3] 添加文件...")
        run_git(["add", "-A"])

        print("\n[2/3] 创建提交...")
        run_git(["commit", "-m", message])

        print("\n[3/3] 上传 GitHub...")
        run_git(["push"])

        print("\n" + "=" * 50)
        print("上传成功！GitHub 仓库已更新。")
        print("=" * 50)
        return 0

    except RuntimeError as error:
        print(f"\n上传未完成：{error}")
        print("\n你可以先运行 git status 查看当前状态，再根据报错处理。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
