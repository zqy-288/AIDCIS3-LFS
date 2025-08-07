#!/usr/bin/env python3
"""
测试P4 PDF支持是否安装成功
"""

def test_pdf_support():
    """测试PDF支持库是否正确安装"""
    print("🔍 检查P4 PDF支持库安装状态...")
    print("=" * 50)
    
    # 测试reportlab
    try:
        import reportlab
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        print("✅ reportlab - PDF核心库安装成功")
        print(f"   版本: {reportlab.Version}")
    except ImportError:
        print("❌ reportlab - PDF核心库未安装")
        print("   安装命令: pip install reportlab")
        return False
    
    # 测试pillow
    try:
        import PIL
        from PIL import Image
        print("✅ Pillow - 图像处理库安装成功")
        print(f"   版本: {PIL.__version__}")
    except ImportError:
        print("❌ Pillow - 图像处理库未安装")
        print("   安装命令: pip install pillow")
    
    # 测试matplotlib
    try:
        import matplotlib
        print("✅ matplotlib - 图表库安装成功")
        print(f"   版本: {matplotlib.__version__}")
    except ImportError:
        print("❌ matplotlib - 图表库未安装")
        print("   安装命令: pip install matplotlib")
    
    # 测试numpy
    try:
        import numpy as np
        print("✅ numpy - 数值计算库安装成功")
        print(f"   版本: {np.__version__}")
    except ImportError:
        print("❌ numpy - 数值计算库未安装")
        print("   安装命令: pip install numpy")
    
    print()
    print("🧪 测试PDF生成功能...")
    
    try:
        # 创建测试PDF
        import tempfile
        import os
        
        temp_file = os.path.join(tempfile.gettempdir(), "test_pdf_support.pdf")
        
        # 创建PDF文档
        c = canvas.Canvas(temp_file, pagesize=letter)
        c.drawString(100, 750, "P4 PDF支持测试成功！")
        c.drawString(100, 730, "Test PDF generation successful!")
        c.save()
        
        if os.path.exists(temp_file):
            print(f"✅ PDF生成测试成功: {temp_file}")
            # 清理测试文件
            os.remove(temp_file)
            return True
        else:
            print("❌ PDF生成测试失败")
            return False
            
    except Exception as e:
        print(f"❌ PDF生成测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_pdf_support()
    
    if success:
        print()
        print("🎉 恭喜！PDF支持安装成功")
        print("现在可以使用P4界面的完整PDF报告功能了")
    else:
        print()
        print("⚠️ PDF支持安装不完整")
        print("请按照上述提示安装缺失的库")