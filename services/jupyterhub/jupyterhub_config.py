# Tệp cấu hình cho JupyterHub
import os

c = get_config()  # noqa: F821

# Khởi chạy các máy chủ đơn người dùng dưới dạng các container Docker
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"

# Khởi chạy các container từ image này
c.DockerSpawner.image = os.environ["DOCKER_NOTEBOOK_IMAGE"]

# Kết nối các container vào mạng Docker này
network_name = os.environ["DOCKER_NETWORK_NAME"]
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = network_name

# Đặt rõ ràng thư mục notebook vì chúng ta sẽ gắn một volume vào nó.
# Hầu hết các image `jupyter/docker-stacks` *-notebook chạy máy chủ Notebook dưới 
# người dùng `jovyan` và đặt thư mục notebook là `/home/jovyan/work`.
# Chúng tôi tuân theo cùng một quy ước này.
notebook_dir = os.environ.get("DOCKER_NOTEBOOK_DIR", "/home/jovyan/work")
c.DockerSpawner.notebook_dir = notebook_dir

# Gắn volume Docker của người dùng thật trên host vào thư mục notebook
# của người dùng trong container
c.DockerSpawner.volumes = {"jupyterhub-user-{username}": notebook_dir}

# Xóa container sau khi chúng bị dừng
c.DockerSpawner.remove = True

# Để gỡ lỗi các tham số được truyền vào container
c.DockerSpawner.debug = True

# Các container người dùng sẽ truy cập hub bằng tên container trong mạng Docker
c.JupyterHub.hub_ip = "jupyterhub"
c.JupyterHub.hub_port = 8080

# Lưu trữ dữ liệu hub trên volume được gắn bên trong container
c.JupyterHub.cookie_secret_file = "/data/jupyterhub_cookie_secret"
c.JupyterHub.db_url = "sqlite:////data/jupyterhub.sqlite"

# Cho phép tất cả người dùng đã đăng ký đăng nhập
c.Authenticator.allow_all = True

# Xác thực người dùng bằng Native Authenticator
c.JupyterHub.authenticator_class = "nativeauthenticator.NativeAuthenticator"

# Cho phép bất kỳ ai đăng ký mà không cần phê duyệt
c.NativeAuthenticator.open_signup = True

# Danh sách quản trị viên được cho phép
admin = os.environ.get("JUPYTERHUB_ADMIN")
if admin:
    c.Authenticator.admin_users = [admin]
