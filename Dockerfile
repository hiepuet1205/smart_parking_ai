# Sử dụng base image Python
FROM python:3.8-slim

# Đặt biến môi trường để đảm bảo output console hoạt động bình thường
ENV PYTHONUNBUFFERED=1

# Tạo thư mục làm việc bên trong container
WORKDIR /app

# Sao chép file requirements.txt vào thư mục làm việc
COPY requirements.txt .

# Cài đặt các dependencies từ requirements.txt
RUN apt-get update && \
    apt-get install -y libgl1 libglib2.0-0 && \
    pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn của ứng dụng vào container
COPY . .

# Expose port 5000 (Flask mặc định chạy trên cổng này)
EXPOSE 5000

# Command để chạy ứng dụng Flask
CMD ["python", "app.py"]
