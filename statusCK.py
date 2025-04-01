# -*- coding: utf-8 -*-
# 导入所需的库
import cv2                      # OpenCV库，用于图像处理和人脸检测
import git                      # GitPython库，用于与Git仓库交互
import os                       # 操作系统库，用于路径操作等
import re                       # 正则表达式库，用于文本匹配和替换
import time                     # 时间库，用于暂停和计时
import logging                  # 日志库，用于记录程序运行信息
from picamera2 import Picamera2 # 树莓派摄像头库 (版本2)
import threading                # 线程库，用于并发执行任务

# 配置日志记录
logging.basicConfig(level=logging.INFO,  # 设置日志级别为INFO，记录INFO及以上级别的日志
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 设置日志格式
                    datefmt='%Y-%m-%d %H:%M:%S',  # 设置时间格式
                    filename='statusCK.log',      # 指定日志输出到文件 statusCK.log
                    filemode='a')                 # 设置文件模式为追加 ('a')

# 常量定义
REPO_PATH = '/home/pi/code/only4john.github.io'  # 本地Git仓库的绝对路径
FILE_REL_PATH = 'zh/index_zh.md'                 # 需要修改的文件相对于仓库根目录的路径
COMMIT_MESSAGE = "Update office status."         # Git提交时使用的固定消息
FONT_SIZE = "16px"                               # 状态指示文字的CSS字体大小
CASCADE_CLASSIFIER_PATH = '/home/pi/code/venv/lib/python3.11/site-packages/cv2/data/haarcascade_frontalface_default.xml' # OpenCV人脸检测模型文件路径
IMAGE_PATH = '/home/pi/code/statusCK/last_face.jpg' # 检测到人脸时保存的图像路径
FACE_CHECK_INTERVAL = 60                         # 人脸检测的间隔时间（秒），即每分钟检查一次
CONSECUTIVE_CHECKS_BEFORE_AWAY = 3               # 连续多少次未检测到人脸后，判定为“不在办公室”

# --- 不再需要 run_git_command 函数 ---

def update_github_page(repo: git.Repo, index_file_rel_path: str, in_office: bool):
    """
    使用GitPython更新GitHub Pages上的状态，并推送更改。
    Args:
        repo (git.Repo): Git仓库对象。
        index_file_rel_path (str): 相对于仓库根目录的目标Markdown文件路径。
        in_office (bool): 当前是否在办公室的状态。
    """
    # 根据状态记录日志
    logging.info(f"开始更新 GitHub 页面状态: {'在办公室' if in_office else '不在办公室'}")
    # 构造文件的完整绝对路径
    index_full_path = os.path.join(repo.working_dir, index_file_rel_path)

    try:
        # --- 文件修改逻辑 ---
        logging.info(f"尝试读取文件: {index_full_path}")
        # 以只读模式打开文件，读取所有行
        with open(index_full_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        logging.info(f"成功从文件读取 {len(lines)} 行。")

        # 查找包含特定标记 "## 费" 的行号
        name_line_index = next(
            (i for i, line in enumerate(lines) if "## 费" in line), -1) # 使用生成器表达式查找，未找到返回-1

        # 如果找到了目标行
        if name_line_index != -1:
            # 根据在办公室状态确定状态文本和颜色
            status_text = "我在办公室里" if in_office else "我不在办公室里"
            status_color = "green" if in_office else "red"
            # 构建新的状态HTML片段
            status_html = (
                f' (<span style="color: {status_color}; font-size: {FONT_SIZE};">&#x25CF;</span>' # 彩色圆点
                f' <span style="font-size: {FONT_SIZE};">{status_text}</span>)\n' # 状态文本
            )
            
            # 使用正则表达式移除该行末尾可能存在的旧的状态HTML片段
            # 正则表达式 `\s*\(<span style=".*?">.*?</span>\)\s*$` 匹配:
            #   \s* - 行尾可能存在的空白字符
            #   \(      - 左括号
            #   <span style=".*?"> - 匹配 <span ...> 标签，非贪婪匹配样式内容
            #   .*?     - 匹配 span 标签内的任何内容，非贪婪
            #   </span> - 匹配 </span> 结束标签
            #   \)      - 右括号
            #   \s* - 行尾可能存在的空白字符
            #   $       - 匹配行尾
            lines[name_line_index] = re.sub(
                r'\s*\(<span style=".*?">.*?</span>\)\s*$', 
                '',  # 替换为空字符串，即删除
                lines[name_line_index].rstrip() # 先移除行尾的空白/换行符再进行替换
            ) + status_html # 将新的状态HTML附加到处理后的行尾

            logging.info(f"已修改行 {name_line_index}: {lines[name_line_index].strip()}")

            # 以写入模式打开文件，将修改后的所有行写回文件
            with open(index_full_path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
            logging.info("文件写入完成。")

        else:
            # 如果未找到目标行，记录警告并返回，不执行Git操作
            logging.warning("在文件中未找到目标行 '## 费'。跳过状态更新。")
            return

        # --- Git 操作 (使用 GitPython) ---
        try:
            logging.info("开始执行 Git 操作 (使用 GitPython)...")

            # 确保 Git 配置已设置 (用户名和邮箱)，仅在需要时设置
            config_writer = repo.config_writer() # 获取配置写入器
            try:
                # 尝试读取用户名，如果失败 (抛异常)，则设置
                config_writer.get_value('user', 'name')
            except Exception: # 捕获通用异常 (更具体的异常可能更好，但这能工作)
                 logging.info("设置 git user.name")
                 config_writer.set_value('user', 'name', 'only4john')
            try:
                # 尝试读取邮箱，如果失败，则设置
                config_writer.get_value('user', 'email')
            except Exception:
                 logging.info("设置 git user.email")
                 config_writer.set_value('user', 'email', 'only4john@gmail.com')
            finally:
                 # 必须释放配置写入器以解除锁定
                 config_writer.release()

            # 1. 添加指定文件到暂存区 (Add)
            logging.info(f"添加文件到 Git 索引: {index_file_rel_path}")
            repo.index.add([index_file_rel_path]) # add方法需要一个列表，包含相对于仓库根的路径

            # 2. 提交更改 (Commit)
            # 提交前检查是否有已暂存的更改
            if repo.is_dirty(index=True): # index=True 检查暂存区
                 logging.info(f"提交更改，提交信息: {COMMIT_MESSAGE}")
                 repo.index.commit(COMMIT_MESSAGE) # 执行提交
            else:
                 logging.info("没有已暂存的更改需要提交。跳过提交。")
                 # 如果没有提交，是否仍要执行pull/push？为了确保同步，我们继续执行。

            # 3. 从远程拉取更改 (Pull)
            # 目的是在推送前合并远程更改，并处理冲突（接受远程版本）
            origin = repo.remotes.origin # 获取名为 'origin' 的远程仓库对象
            logging.info("从远程 origin 拉取更改。")
            try:
                 # GitPython 的 pull 不直接支持 strategy-option。
                 # 这里的策略是：先执行普通的 pull。
                 pull_info = origin.pull() # 执行 pull
                 logging.info(f"Pull 完成: {pull_info}")
                 # Pull 后，可能文件内容被改变（例如合并），因此需要重新将我们期望的文件状态添加到暂存区
                 logging.info(f"Pull 后重新添加文件 {index_file_rel_path} 以确保我们的状态被暂存。")
                 repo.index.add([index_file_rel_path])
                 # 如果 Pull 导致了合并提交或其他更改，可能需要重新提交我们的文件状态
                 if repo.is_dirty(index=True):
                     logging.info(f"Pull 后重新提交更改，提交信息: {COMMIT_MESSAGE}")
                     repo.index.commit(COMMIT_MESSAGE)

            except git.GitCommandError as pull_err:
                 logging.error(f"Git pull 失败: {pull_err}")
                 # 记录错误，但仍尝试执行 push
            except Exception as e:
                 logging.error(f"Pull 过程中发生意外错误: {e}")

            # 4. 推送更改到远程仓库 (Push)
            logging.info("推送更改到远程 origin。")
            push_info = origin.push() # 执行 push
            # push_info 包含推送结果的详细信息
            logging.info(f"Push 完成: {push_info}")

            logging.info('GitHub 页面更新流程通过 GitPython 成功完成！')

        except git.GitCommandError as git_err:
            # 捕获 GitPython 命令执行错误
            logging.error(f'更新过程中发生 GitPython 命令错误: {git_err}')
            # 考虑是否需要重置 HEAD 来避免仓库处于不良状态，例如：
            # repo.git.reset('--hard') # 注意：这个命令很危险，会丢弃本地更改！
        except Exception as general_err:
            # 捕获其他 Git 操作中的常规错误
            logging.error(f'Git 操作过程中发生错误: {general_err}')

    except FileNotFoundError:
        # 捕获文件未找到的错误
        logging.error(f"错误: 文件未找到 {index_full_path}")
    except Exception as e:
        # 捕获 update_github_page 函数中的其他未预期错误
        logging.error(f"update_github_page 函数出错: {e}")

    finally:
        # 无论成功或失败，都记录函数结束
        logging.info("update_github_page 函数执行完毕")


def process_frames(picam2: Picamera2, detector: cv2.CascadeClassifier, repo: git.Repo, index_file_rel_path: str) -> None:
    """
    处理摄像头帧，检测人脸，并根据新的逻辑更新GitHub状态。
    Args:
        picam2 (Picamera2): Picamera2 摄像头对象。
        detector (cv2.CascadeClassifier): OpenCV 人脸检测器。
        repo (git.Repo): Git 仓库对象。
        index_file_rel_path (str): 状态文件的相对路径。
    """
    logging.info("启动图像处理循环 (使用新逻辑)。")

    try:
        # 初始化状态变量
        in_office = True  # 默认状态为“在办公室”
        no_face_counter = 0 # 未检测到人脸的连续次数计数器
        # 构造文件的完整路径，供后续使用
        full_file_path = os.path.join(repo.working_dir, index_file_rel_path)

        # 程序启动时，立即更新一次状态为默认的“在办公室”
        logging.info("设置初始状态为 '在办公室'。")
        update_github_page(repo, index_file_rel_path, True)

        # 启动摄像头
        picam2.start()
        logging.info("摄像头已为处理循环启动。")

        # 无限循环，持续处理图像
        while True:
            start_time = time.time() # 记录循环开始时间
            # 捕捉摄像头帧
            try:
                logging.debug("正在捕捉帧...")
                frame = picam2.capture_array() # 从摄像头获取图像数据 (NumPy 数组)
                # 检查是否成功获取帧
                if frame is None:
                    logging.error("未能捕捉到帧。")
                    # 等待一段时间再重试，避免错误信息刷屏
                    time.sleep(FACE_CHECK_INTERVAL / 2) # 等待半个检测周期
                    continue # 跳过本次循环的剩余部分
                logging.debug("帧捕捉成功。")
            except Exception as capture_error:
                # 捕获捕捉帧时可能发生的错误
                logging.error(f"捕捉帧时发生错误: {capture_error}")
                time.sleep(FACE_CHECK_INTERVAL / 2) # 等待半个检测周期
                continue # 跳过本次循环

            # 处理帧：转换为灰度图，然后检测人脸
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # 转换为灰度图像，提高检测效率
            # 使用级联分类器检测人脸，返回找到的人脸矩形列表
            faces = detector.detectMultiScale(gray_frame, 1.1, 4) # scaleFactor=1.1, minNeighbors=4

            # 根据是否检测到人脸以及计数器状态，更新办公室状态
            if len(faces) > 0: # 如果检测到至少一张人脸
                logging.info(f"检测到人脸 ({len(faces)} 张). 重置 no_face_counter 为 0。")
                no_face_counter = 0  # 重置连续未检测计数器
                # 可以选择性地保存检测到人脸的图像
                cv2.imwrite(IMAGE_PATH, frame)

                # 检查：如果当前状态是“不在办公室”，则更新为“在办公室”
                if not in_office:
                    logging.info("检测到人脸，且当前状态为 '不在办公室'。将状态更改为 '在办公室'。")
                    in_office = True # 更新内存中的状态
                    # 调用函数更新 GitHub 页面
                    update_github_page(repo, index_file_rel_path, True)
                # 如果本来就在办公室，则无需操作

            else: # 如果没有检测到人脸
                no_face_counter += 1 # 连续未检测计数器加 1
                logging.info(f"未检测到人脸。计数器: {no_face_counter}/{CONSECUTIVE_CHECKS_BEFORE_AWAY}")

                # 检查：如果计数器达到阈值，并且当前状态是“在办公室”，则更新为“不在办公室”
                if no_face_counter >= CONSECUTIVE_CHECKS_BEFORE_AWAY and in_office:
                    logging.info(f"连续 {CONSECUTIVE_CHECKS_BEFORE_AWAY} 次未检测到人脸。将状态更改为 '不在办公室'。")
                    in_office = False # 更新内存中的状态
                    # 调用函数更新 GitHub 页面
                    update_github_page(repo, index_file_rel_path, False)
                # 如果本来就不在办公室，或者计数器未达到阈值，则无需操作

            # 控制循环频率：计算本次循环花费的时间，然后睡眠剩余时间以达到 FACE_CHECK_INTERVAL
            elapsed_time = time.time() - start_time # 计算循环耗时
            # 计算需要睡眠的时间，确保总时长约为 FACE_CHECK_INTERVAL
            # max(0, ...) 防止耗时超过间隔导致睡眠时间为负
            sleep_duration = max(0, FACE_CHECK_INTERVAL - elapsed_time)
            logging.debug(f"本次循环耗时 {elapsed_time:.2f}秒. 睡眠 {sleep_duration:.2f}秒.")
            time.sleep(sleep_duration) # 暂停执行

    except KeyboardInterrupt:
        # 捕获 Ctrl+C 中断信号
        logging.info("用户通过键盘中断 (Ctrl+C) 停止脚本。")
    except Exception as general_error:
        # 捕获 process_frames 循环中未处理的其他异常
        # 使用 exc_info=True 记录完整的错误堆栈信息
        logging.critical(f"process_frames 循环中发生未处理错误: {general_error}", exc_info=True)
    finally:
        # 无论循环如何退出（正常结束、异常、中断），都执行清理操作
        logging.info("正在关闭 process_frames 中的摄像头资源...")
        try:
            # 检查摄像头是否已启动，避免对未启动的摄像头执行 stop
            if picam2.started:
                 picam2.stop() # 停止摄像头
                 logging.info("摄像头已停止。")
            # Picamera2 较新版本可能没有 stop_and_close()，stop() 通常足够
        except Exception as close_error:
            # 捕获停止摄像头时可能发生的错误
            logging.error(f"停止摄像头资源时发生错误: {close_error}")
        logging.info("函数 'process_frames' 即将结束。")

# 主程序入口
if __name__ == "__main__":
    try:
        logging.info("启动状态检查程序")

        # 初始化摄像头
        picam2 = Picamera2()
        logging.info("摄像头对象已创建")
        # 创建摄像头配置 (预览模式，用于获取图像数组)
        camConfig = picam2.create_preview_configuration(
            main={"format": 'XRGB8888', "size": (1280, 720)} # 设置像素格式和分辨率
        )
        logging.info("摄像头配置对象已创建")
        # 应用配置
        picam2.configure(camConfig)
        logging.info("摄像头配置已应用")
        # 注意：摄像头在这里只配置，不在主线程启动，而是在 process_frames 线程中启动

        # 初始化人脸检测器
        face_cascade = cv2.CascadeClassifier(CASCADE_CLASSIFIER_PATH) # 加载模型文件
        # 检查模型是否加载成功
        if face_cascade.empty():
             logging.critical(f"无法从 {CASCADE_CLASSIFIER_PATH} 加载级联分类器")
             raise RuntimeError("无法加载人脸级联分类器。") # 抛出运行时错误
        logging.info("人脸检测器初始化成功")

        # 初始化 Git 仓库对象
        try:
            repo = git.Repo(REPO_PATH) # 创建仓库对象
            logging.info(f"Git 仓库初始化成功，路径: {REPO_PATH}")
        except git.InvalidGitRepositoryError:
            # 如果指定路径不是有效的 Git 仓库
            logging.critical(f"路径 {REPO_PATH} 不是有效的 Git 仓库")
            raise # 重新抛出异常
        except Exception as repo_err:
             # 捕获其他初始化仓库时可能发生的错误
             logging.critical(f"初始化 Git 仓库失败: {repo_err}")
             raise

        # --- 移除调度器相关代码 ---

        # 创建并启动处理帧的线程
        # target=process_frames 指定线程要执行的函数
        # args=(...) 传递给函数的参数元组，注意包含 repo 对象和文件相对路径
        # daemon=True 将线程设置为守护线程，主线程退出时该线程也会强制退出
        thread = threading.Thread(target=process_frames, args=(picam2, face_cascade, repo, FILE_REL_PATH), daemon=True)
        logging.info("正在启动处理线程...")
        thread.start() # 启动线程
        logging.info("处理线程已启动")

        # 主线程需要保持运行，以让守护线程继续工作
        # 使用 join() 的循环可以允许主线程响应 KeyboardInterrupt
        while thread.is_alive(): # 当处理线程仍在运行时
            try:
                # 等待线程结束，设置超时时间（例如1秒）
                # 这使得循环可以定期检查 KeyboardInterrupt
                thread.join(timeout=1.0)
            except KeyboardInterrupt:
                # 如果在主线程等待时收到 Ctrl+C
                logging.info("在主线程中收到键盘中断。开始关闭...")
                # 因为线程是守护线程，理论上主线程结束它就会结束
                # 如果需要更优雅的停止，需要在 process_frames 中实现停止逻辑 (例如设置一个全局标志)
                break # 跳出循环，主线程将结束

    except Exception as startup_error:
        # 捕获启动过程中发生的严重错误
        logging.critical(f"程序启动时发生严重错误: {startup_error}", exc_info=True) # 记录堆栈信息
    finally:
        # 最后的清理工作，确保资源被释放
        # 检查 picam2 变量是否存在且摄像头是否仍在运行 (以防主线程异常退出)
        if 'picam2' in locals() and picam2.started:
            try:
                picam2.stop() # 尝试停止摄像头
                logging.info("在最终关闭阶段停止了摄像头。")
            except Exception as e:
                logging.error(f"在最终关闭阶段停止摄像头时出错: {e}")
        logging.info("状态检查程序正在关闭")