import cv2
import numpy as np
import logging
from pathlib import Path
from tqdm import tqdm
from image_processor.deblur import DeblurProcessor
from image_processor.unwrap import UnwrapProcessor
from image_processor.stitch import StitchProcessor
from utils.logger import setup_logger
from utils.config import Config

def calculate_frame_similarity(frame1, frame2):
    """计算两帧之间的相似度（使用直方图相关性）"""
    # 转换为灰度图
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY) if len(frame1.shape) == 3 else frame1
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY) if len(frame2.shape) == 3 else frame2
    
    # 计算直方图
    hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
    
    # 计算相关性
    correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    return correlation

def calculate_frame_motion(frame1, frame2):
    """计算两帧之间的运动量（使用帧差）"""
    # 转换为灰度图
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY) if len(frame1.shape) == 3 else frame1
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY) if len(frame2.shape) == 3 else frame2
    
    # 使用帧差计算运动量
    diff = cv2.absdiff(gray1, gray2)
    motion_magnitude = np.mean(diff) / 255.0
    return motion_magnitude

def select_keyframes_interval(frame_indices, config):
    """基于固定间隔选择关键帧"""
    selected_indices = []
    for i in range(0, len(frame_indices), config.keyframe_interval):
        selected_indices.append(frame_indices[i])
        if len(selected_indices) >= config.max_keyframes:
            break
    return selected_indices

def select_keyframes_similarity(frames_data, config):
    """基于相似度选择关键帧"""
    if not frames_data:
        return []
    
    selected_indices = [frames_data[0]['index']]  # 总是选择第一帧
    last_selected_frame = frames_data[0]['frame']
    
    for i in range(1, len(frames_data)):
        current_frame = frames_data[i]['frame']
        similarity = calculate_frame_similarity(last_selected_frame, current_frame)
        
        # 如果相似度低于阈值，说明变化较大，选择该帧
        if similarity < (1.0 - config.similarity_threshold):
            selected_indices.append(frames_data[i]['index'])
            last_selected_frame = current_frame
            
            if len(selected_indices) >= config.max_keyframes:
                break
    
    return selected_indices

def select_keyframes_motion(frames_data, config):
    """基于运动检测选择关键帧"""
    if len(frames_data) < 2:
        return [frames_data[0]['index']] if frames_data else []
    
    selected_indices = [frames_data[0]['index']]  # 总是选择第一帧
    last_selected_frame = frames_data[0]['frame']
    
    for i in range(1, len(frames_data)):
        current_frame = frames_data[i]['frame']
        motion = calculate_frame_motion(last_selected_frame, current_frame)
        
        # 如果运动量超过阈值，选择该帧
        if motion > config.motion_threshold:
            selected_indices.append(frames_data[i]['index'])
            last_selected_frame = current_frame
            
            if len(selected_indices) >= config.max_keyframes:
                break
    
    return selected_indices

def select_keyframes(cap, start_frame, end_frame, config):
    """选择关键帧"""
    logger = logging.getLogger(__name__)
    
    if not config.enable_keyframe_selection:
        # 如果未启用关键帧选择，返回所有帧索引
        all_indices = list(range(start_frame, end_frame))
        logger.info(f"关键帧选择已禁用，将处理所有 {len(all_indices)} 帧")
        return all_indices
    
    logger.info(f"开始关键帧选择，策略: {config.keyframe_strategy}")
    
    # 如果是固定间隔策略，不需要加载所有帧
    if config.keyframe_strategy == "interval":
        all_indices = list(range(start_frame, end_frame))
        selected = select_keyframes_interval(all_indices, config)
        logger.info(f"固定间隔选择完成，从 {len(all_indices)} 帧中选择了 {len(selected)} 帧")
        return selected
    
    # 对于相似度和运动检测策略，需要预读取部分帧数据
    frames_data = []
    sample_interval = max(1, (end_frame - start_frame) // 200)  # 最多采样200帧进行分析
    
    logger.info(f"预读取帧数据进行分析，采样间隔: {sample_interval}")
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_index = start_frame
    
    with tqdm(total=(end_frame - start_frame) // sample_interval, desc="分析帧特征") as pbar:
        while current_index < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 缩小帧尺寸以节省内存
            small_frame = cv2.resize(frame, (320, 240))
            frames_data.append({
                'index': current_index,
                'frame': small_frame
            })
            
            # 跳到下一个采样点
            current_index += sample_interval
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_index)
            pbar.update(1)
            
            # 防止内存溢出
            if len(frames_data) >= 200:
                break
    
    # 根据策略选择关键帧
    if config.keyframe_strategy == "similarity":
        selected = select_keyframes_similarity(frames_data, config)
        logger.info(f"基于相似度选择完成，从 {len(frames_data)} 个采样帧中选择了 {len(selected)} 帧")
    elif config.keyframe_strategy == "motion":
        selected = select_keyframes_motion(frames_data, config)
        logger.info(f"基于运动检测选择完成，从 {len(frames_data)} 个采样帧中选择了 {len(selected)} 帧")
    else:
        raise ValueError(f"未知的关键帧选择策略: {config.keyframe_strategy}")
    
    return selected

def process_video(video_path: str, output_dir: str, config: Config):
    """
    处理视频文件的主函数
    
    Args:
        video_path: 输入视频路径
        output_dir: 输出目录
        config: 配置对象
        
    Returns:
        (panorama, summary): 全景图和处理摘要
    """
    logger = logging.getLogger(__name__)
    logger.info(f"开始处理视频: {video_path}")
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 创建各阶段结果保存目录
    if config.save_intermediate:
        deblurred_dir = output_path / "01_deblurred"
        unwrapped_dir = output_path / "02_unwrapped"
        stitch_dir=output_path / "04_stitched"
        deblurred_dir.mkdir(exist_ok=True)
        unwrapped_dir.mkdir(exist_ok=True)
        stitch_dir.mkdir(exist_ok=True)

    
    # 初始化处理器
    deblur_processor = DeblurProcessor(config)
    unwrap_processor = UnwrapProcessor(config)
    stitch_processor = StitchProcessor(config)
    
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_seconds = total_frames / fps if fps > 0 else 0

    # 计算时间段对应的帧范围
    start_frame = int(config.start_time_seconds * fps)
    end_frame = int(config.end_time_seconds * fps)
    
    # 验证时间段有效性
    if config.start_time_seconds < 0:
        raise ValueError(f"开始时间不能为负数: {config.start_time_seconds}")
    if config.end_time_seconds <= config.start_time_seconds:
        raise ValueError(f"结束时间({config.end_time_seconds})必须大于开始时间({config.start_time_seconds})")
    if config.start_time_seconds >= duration_seconds:
        raise ValueError(f"开始时间({config.start_time_seconds}s)超出视频长度({duration_seconds:.2f}s)")
    
    # 调整结束时间不超过视频长度
    actual_end_time = min(config.end_time_seconds, duration_seconds)
    end_frame = min(end_frame, total_frames)
    total_frames_in_range = end_frame - start_frame
    
    logger.info(f"视频信息:")
    logger.info(f"  - FPS: {fps:.2f}")
    logger.info(f"  - 总帧数: {total_frames}")
    logger.info(f"  - 视频时长: {duration_seconds:.2f}秒")
    logger.info(f"处理时间段: {config.start_time_seconds:.2f}s - {actual_end_time:.2f}s")
    logger.info(f"对应帧范围: {start_frame} - {end_frame} (共{total_frames_in_range}帧)")
    
    # 选择关键帧
    keyframe_indices = select_keyframes(cap, start_frame, end_frame, config)
    logger.info(f"最终选择了 {len(keyframe_indices)} 个关键帧进行处理")
    
    if not keyframe_indices:
        raise ValueError("没有选择到任何关键帧")
    
    processed_frames = []
    frame_count = 0
    
    with tqdm(total=len(keyframe_indices), desc=f"处理关键帧 ({config.start_time_seconds:.1f}s-{actual_end_time:.1f}s)") as pbar:
        for frame_index in keyframe_indices:
            # 定位到指定帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()
            
            if not ret:
                logger.warning(f"无法读取帧{frame_index} (时间: {frame_index/fps:.2f}s)")
                continue

            try:
                # 1. 图像增强（去模糊）
                current_time = frame_index / fps
                logger.info(f"处理关键帧{frame_index} (时间: {current_time:.2f}s) - 去模糊增强")
                enhanced = deblur_processor.process(frame, frame_count, output_path)
                
                # 保存增强结果
                if config.save_intermediate:
                    enhanced_path = deblurred_dir / f"enhanced_{frame_count:04d}.{config.output_format}"
                    cv2.imwrite(str(enhanced_path), enhanced)
                    logger.info(f"保存去模糊图像: {enhanced_path}")
                
                # 收集增强后的图像，稍后一次性进行展平处理
                processed_frames.append(enhanced)
                
            except Exception as e:
                logger.error(f"处理关键帧{frame_index} (时间: {current_time:.2f}s)时出错: {str(e)}")
                continue
            
            frame_count += 1
            pbar.update(1)
    
    cap.release()
    
    if not processed_frames:
        raise ValueError("没有成功处理的关键帧")
    
    # 2. 批量处理图像展平
    logger.info(f"开始展平 {len(processed_frames)} 张增强后的图像")
    unwrapped_frames = unwrap_processor.process(processed_frames, output_path)
    logger.info(f"图像展平完成，处理了 {len(unwrapped_frames)} 张图像")
    
    # 3. 图像拼接
    logger.info(f"开始拼接 {len(unwrapped_frames)} 张展平后的图像")
    panorama = stitch_processor.process(unwrapped_frames, output_path)
    
    # 保存最终结果
    if config.output_format.lower() == "tiff":
        output_file = output_path / "panorama.tiff"
        cv2.imwrite(str(output_file), panorama, [cv2.IMWRITE_TIFF_COMPRESSION, 1])
    else:
        output_file = output_path / f"panorama.{config.output_format}"
        cv2.imwrite(str(output_file), panorama, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    
    logger.info(f"全景图已保存至: {output_file}")
    
    # 保存配置文件以便追溯
    config.save_json(str(output_path / "config.json"))
    
    # 返回处理摘要
    summary = {
        'total_frames_in_range': total_frames_in_range,
        'keyframes_selected': len(keyframe_indices),
        'processed_frames': len(processed_frames),
        'panorama_size': panorama.shape,
        'output_file': str(output_file),
        'keyframe_strategy': config.keyframe_strategy if config.enable_keyframe_selection else 'all_frames'
    }
    
    return panorama, summary

def main():
    # 设置日志
    setup_logger()
    logger = logging.getLogger(__name__)
    
    # 加载配置
    config = Config()
    
    # 验证配置
    config.validate()
    
    # 显示配置摘要
    logger.info(config.get_processing_summary())
    
    # 处理视频
    video_path = "final.mp4"  # 视频文件路径
    output_dir = "output_final"
    
    try:
        logger.info("=" * 60)
        logger.info("工业内窥镜图像处理系统启动")
        logger.info("=" * 60)
        
        panorama, summary = process_video(video_path, output_dir, config)
        
        logger.info("=" * 60)
        logger.info("处理完成，结果摘要:")
        logger.info(f"- 时间段总帧数: {summary['total_frames_in_range']}")
        logger.info(f"- 选择关键帧数: {summary['keyframes_selected']}")
        logger.info(f"- 成功处理帧数: {summary['processed_frames']}")
        logger.info(f"- 关键帧策略: {summary['keyframe_strategy']}")
        logger.info(f"- 全景图尺寸: {summary['panorama_size']}")
        logger.info(f"- 输出文件: {summary['output_file']}")
        if config.enable_keyframe_selection:
            reduction_ratio = summary['keyframes_selected'] / summary['total_frames_in_range'] * 100
            logger.info(f"- 处理帧数减少: {100-reduction_ratio:.1f}% (内存优化效果)")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"处理过程中出现错误: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 