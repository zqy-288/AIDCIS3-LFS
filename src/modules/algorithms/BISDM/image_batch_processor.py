import cv2
import numpy as np
import os
import glob
import logging
from pathlib import Path
from tqdm import tqdm
from image_processor.deblur import DeblurProcessor
from image_processor.unwrap import UnwrapProcessor
from image_processor.stitch import StitchProcessor
from utils.logger import setup_logger
from utils.config import Config

class ImageBatchProcessor:
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化处理器
        self.deblur_processor = DeblurProcessor(config)
        self.unwrap_processor = UnwrapProcessor(config)
        self.stitch_processor = StitchProcessor(config)
    
    def process_images_folder(self, input_dir: str, output_dir: str):
        """
        处理图像文件夹
        
        Args:
            input_dir: 输入图像文件夹路径
            output_dir: 输出目录路径
        """
        self.logger.info(f"开始处理图像文件夹: {input_dir}")
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 创建各阶段结果保存目录
        if self.config.save_intermediate:
            deblurred_dir = output_path / "01_deblurred"
            unwrapped_dir = output_path / "02_unwrapped"
            stitch_dir = output_path / "03_stitch_intermediate"
            deblurred_dir.mkdir(exist_ok=True)
            unwrapped_dir.mkdir(exist_ok=True)
            stitch_dir.mkdir(exist_ok=True)
        
        # 获取所有图像文件（修复重复问题）
        image_paths = []
        # 只搜索常见的图像格式，避免重复
        for pattern in ["*.jpg", "*.png", "*.jpeg", "*.bmp"]:
            image_paths.extend(glob.glob(os.path.join(input_dir, pattern)))
        
        # 去重并按文件名排序
        image_paths = sorted(list(set(image_paths)))
        
        if not image_paths:
            raise ValueError(f"在目录 {input_dir} 中未找到图像文件")
        
        self.logger.info(f"找到 {len(image_paths)} 张唯一图像")
        self.logger.info(f"图像文件: {[os.path.basename(p) for p in image_paths[:5]]}...")  # 显示前5个
        
        processed_frames = []
        
        # 处理每张图像
        with tqdm(total=len(image_paths), desc="处理图像") as pbar:
            for frame_idx, image_path in enumerate(image_paths):
                self.logger.info(f"处理图像 {frame_idx + 1}/{len(image_paths)}: {os.path.basename(image_path)}")
                
                # 读取图像
                image = cv2.imread(image_path)
                if image is None:
                    self.logger.warning(f"无法读取图像: {image_path}")
                    continue
                
                try:
                    # 1. 图像增强（去模糊）
                    self.logger.info(f"处理第{frame_idx}张图像 - 去模糊增强")
                    enhanced = self.deblur_processor.process(image, frame_idx)
                    
                    # 保存增强结果
                    if self.config.save_intermediate:
                        enhanced_path = deblurred_dir / f"enhanced_{frame_idx:04d}.{self.config.output_format}"
                        cv2.imwrite(str(enhanced_path), enhanced)
                    
                    # 2. 图像展平
                    self.logger.info(f"处理第{frame_idx}张图像 - 柱面展开")
                    unwrapped_list = self.unwrap_processor.process([enhanced], output_path)
                    unwrapped = unwrapped_list[0]  # 取第一个（也是唯一的）结果
                    
                    # 保存展平结果
                    if self.config.save_intermediate:
                        unwrapped_path = unwrapped_dir / f"unwrapped_{frame_idx:04d}.{self.config.output_format}"
                        cv2.imwrite(str(unwrapped_path), unwrapped)
                        self.logger.info(f"保存展平图像: {unwrapped_path}")
                    
                    processed_frames.append(unwrapped)
                    
                except Exception as e:
                    self.logger.error(f"处理图像 {image_path} 时出错: {str(e)}")
                    continue
                
                pbar.update(1)
        
        if not processed_frames:
            raise ValueError("没有成功处理的图像")
        
        # 3. 图像拼接
        self.logger.info(f"开始拼接 {len(processed_frames)} 张图像")
        panorama = self.stitch_processor.process(processed_frames, output_path)
        
        # 保存最终结果
        if self.config.output_format.lower() == "tiff":
            output_file = output_path / "panorama.tiff"
            cv2.imwrite(str(output_file), panorama, [cv2.IMWRITE_TIFF_COMPRESSION, 1])
        else:
            output_file = output_path / f"panorama.{self.config.output_format}"
            cv2.imwrite(str(output_file), panorama, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        
        self.logger.info(f"全景图已保存至: {output_file}")
        
        # 保存配置文件以便追溯
        self.config.save_json(str(output_path / "config.json"))
        
        # 返回处理摘要
        summary = {
            'input_images': len(image_paths),
            'processed_images': len(processed_frames),
            'panorama_size': panorama.shape,
            'output_file': str(output_file)
        }
        
        return panorama, summary

def main():
    """主函数 - 处理imgs文件夹"""
    # 设置日志
    setup_logger()
    logger = logging.getLogger(__name__)
    
    # 加载配置
    config = Config()
    
    # 创建批量处理器
    processor = ImageBatchProcessor(config)
    
    # 处理imgs文件夹
    input_dir = "imgs"
    output_dir = "output_batch"
    
    try:
        logger.info("=" * 60)
        logger.info("批量图像处理系统启动")
        logger.info("=" * 60)
        
        panorama, summary = processor.process_images_folder(input_dir, output_dir)
        
        logger.info("=" * 60)
        logger.info("处理完成，结果摘要:")
        logger.info(f"- 输入目录: {input_dir}")
        logger.info(f"- 输入图像数: {summary['input_images']}")
        logger.info(f"- 成功处理数: {summary['processed_images']}")
        logger.info(f"- 全景图尺寸: {summary['panorama_size']}")
        logger.info(f"- 输出文件: {summary['output_file']}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"处理过程中出现错误: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 