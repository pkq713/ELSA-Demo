import os
import subprocess
from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd

app = Flask(__name__)

# 设置上传文件夹和允许的文件扩展名
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'txt'}

# 创建上传文件夹和输出文件夹
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_lsa_to_csv(lsa_file, csv_file):
    lsa_df = pd.read_csv(lsa_file, sep='\t', header=0)
    lsa_df.to_csv(csv_file, index=False)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute_lsa():
    try:
        # 获取表单数据
        lsa_input = request.files['lsa_input']
        delaylimit = request.form.get('delaylimit', '')
        repnum = request.form.get('repnum', '')
        spotnum = request.form.get('spotnum', '')

        # 检查文件是否存在且是允许的类型
        if lsa_input and allowed_file(lsa_input.filename):
            # 保存文件
            input_filename = os.path.join(app.config['UPLOAD_FOLDER'], lsa_input.filename)
            lsa_input.save(input_filename)

            # 生成唯一的输出文件名
            base_filename = os.path.splitext(lsa_input.filename)[0]
            lsa_output_filename = os.path.join(app.config['OUTPUT_FOLDER'], f"{base_filename}.lsa")
            csv_output_filename = os.path.join(app.config['OUTPUT_FOLDER'], f"{base_filename}.csv")

            # 构建命令
            command = [
                'lsa_compute',
                input_filename,
                csv_output_filename
            ]

            # 动态添加用户输入的参数
            if delaylimit:
                command.extend(['-d', delaylimit])
            if repnum:
                command.extend(['-r', repnum])
            if spotnum:
                command.extend(['-s', spotnum])

            print("Constructed command:", command)
            result = subprocess.run(command, capture_output=True, text=True)

            convert_lsa_to_csv(lsa_output_filename, csv_output_filename)

            # 返回脚本的输出结果和下载链接
            download_link = f"/download/{os.path.basename(csv_output_filename)}"
            response = {
                'data_received': {
                    'delaylimit': delaylimit,
                    'repnum': repnum,
                    'spotnum': spotnum,
                    'input_filename': input_filename,
                    'output_filename': csv_output_filename
                },
                'stdout': result.stdout,
                'stderr': result.stderr,
                'download_link': download_link
            }
            return jsonify(response), 200
        else:
            return jsonify({"error": "Invalid file type. Only .txt files are allowed."}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename), as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)