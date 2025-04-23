from flask import Flask, request, render_template, flash, redirect, send_file
import os
import sys

# Add the modules directory to Python's module search path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from imefim_logic import run_imefim

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for flashing messages
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Ensure upload and result directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route('/')
def about_us():
    return render_template('about_us.html')

@app.route('/huis', methods=['GET', 'POST'])
def index():
    result_content = None  # Nội dung file kết quả
    result_file_path = None  # Đường dẫn file kết quả
    result_file_name = None  # Tên file kết quả

    if request.method == 'POST':
        # Kiểm tra xem file và giá trị minutil có tồn tại không
        if 'file' not in request.files or 'minutil' not in request.form:
            flash("Error: Missing file or minutil.")
            return redirect('/huis')

        uploaded_file = request.files['file']
        try:
            minutil = float(request.form.get('minutil'))
        except ValueError:
            flash("Error: Invalid minimum utility threshold (minutil).")
            return redirect('/huis')

        # Kiểm tra file hợp lệ
        if uploaded_file.filename == '':
            flash("Error: No file selected.")
            return redirect('/huis')

        if uploaded_file.content_length > MAX_FILE_SIZE:
            flash("Error: File size exceeds 5 MB.")
            return redirect('/huis')

        # Lưu file tải lên
        input_file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
        uploaded_file.save(input_file_path)

        # Chạy mô hình iMEFIM
        try:
            result = run_imefim(input_file_path, minutil)
        except Exception as e:
            flash(f"Error running the model: {e}")
            return redirect('/huis')

        # Lưu kết quả vào file (dù có rỗng cũng phải tạo file)
        result_file_name = f"{os.path.splitext(uploaded_file.filename)[0]}_Result.txt"
        result_file_path = os.path.join(RESULT_FOLDER, result_file_name)
        try:
            with open(result_file_path, 'w') as result_file_obj:
                if result:
                    for itemset, utility in result:
                        result_file_obj.write(f"{itemset} {utility}\n")
                else:
                    result_file_obj.write("")  # Tạo file rỗng nếu không có kết quả

            # Đọc nội dung file để hiển thị trên trang
            with open(result_file_path, 'r') as result_file_obj:
                result_content = result_file_obj.read()
        except Exception as e:
            flash(f"Error writing result file: {e}")
            return redirect('/huis')

    return render_template(
        'find_huis.html',
        result_content=result_content,
        result_file_path=result_file_path,
        result_file_name=result_file_name
    )

@app.route('/download_result')
def download_result():
    result_file_path = request.args.get('file_path')  # Lấy đường dẫn file từ query parameter
    if result_file_path and os.path.exists(result_file_path):
        return send_file(result_file_path, as_attachment=True)
    else:
        flash("Result file not found!")
        return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
