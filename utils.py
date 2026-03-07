import shutil
import os
import re
import glob
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
class Utils:
    # 将一个文件夹下的文件或一个文件放到另一个文件夹中
    @staticmethod
    def copy_files(source, destination):

      # 确保目标文件夹存在，如果不存在就创建它
      if not os.path.exists(destination):
            os.makedirs(destination)
      if os.path.isdir(source):
        # 如果源是文件夹，使用 copytree 复制整个文件夹
        shutil.copytree(source, os.path.join(destination, os.path.basename(source)))
      elif os.path.isfile(source):
            # 如果源是文件，使用 copy 复制文件
            shutil.copy(source, os.path.join(destination, os.path.basename(source)))
      else:
        print("源路径无效，文件或文件夹不存在。")

    # 将一个文件夹下的所有内容（包括子文件夹和文件）复制到另一个文件夹中
    def copy_dir_contents(source_dir, destination):
        os.makedirs(destination, exist_ok=True)
        for name in os.listdir(source_dir):
            src = os.path.join(source_dir, name)
            dst = os.path.join(destination, name)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)


    # 提取ai_response_s5中的csv代码块，将其保存为.csv文件
    @staticmethod
    def extract_csv_from_response(response_file, csv_file_path):
        with open(response_file, "r", encoding="utf-8") as f:
            content = f.read()
        # 使用正则表达式提取csv代码块
        csv_content = re.findall(r"```csv\n(.*?)```", content, re.DOTALL)
        # 获取文件夹路径
        folder_path = os.path.dirname(csv_file_path)
        # 如果文件夹不存在，创建文件夹
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        if csv_content:
            with open(csv_file_path, "w", encoding="utf-8") as f:
                f.write(csv_content[0])


    # 更新测试用例结果文件，使之适应matlab仿真的输入格式
    @staticmethod
    def organize_testcase_files(exp_dir):
        model_dir = os.path.join(exp_dir, "model")
        testcase_dir = [
                        os.path.join(exp_dir, "ai_response_s3_testcase"),
       
                        ]
        num = 1;
        dst_dir = os.path.join(model_dir, 'testcase')
        os.makedirs(dst_dir, exist_ok=True)  
        for testcase_path in testcase_dir:
            if os.path.exists(testcase_path):
                
                csv_files = glob.glob(testcase_path + "/*.csv")
                for file_name in csv_files:
                    source_file = file_name
                    dest_file = os.path.join(model_dir, 'testcase',f'S{num}_tc.csv')
                    
                    shutil.copy2(source_file, dest_file)
                    num = num + 1
        
    # 将docx文件转换为文本字符串
    @staticmethod
    def docx_to_text(docx_file):
        doc = Document(docx_file)
        lines = []
        table_idx = 1

        for block in Utils.iter_blocks(doc):
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if text:
                    lines.append(text)
            elif isinstance(block, Table):
                lines.append(f"===== TABLE {table_idx} =====")
                for row in block.rows:
                    cells = [" ".join(p.text for p in cell.paragraphs).strip()
                            for cell in row.cells]
                    lines.append("\t".join(cells))
                table_idx += 1
        text_str = "\n".join(lines)
        return text_str

    @classmethod
    def iter_blocks(cls, doc):
        for block in doc.element.body:
            if block.tag.endswith('p'):
                yield Paragraph(block, doc)
            elif block.tag.endswith('tbl'):
                yield Table(block, doc)