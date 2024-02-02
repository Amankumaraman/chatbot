workers = 4  # Adjust the number of workers based on your machine's capabilities
bind = "0.0.0.0:8000"  # Specify the IP address and port where Gunicorn will listen
chdir = "C:\Users\amank\OneDrive\Desktop\chat pdf django user login - Copy"  # Set the path to your Django project's directory
module = "chatpdfproject.wsgi:application"  # Specify the WSGI module path

# Additional Gunicorn settings (optional)
# loglevel = "error"
# errorlog = "C:/path/to/error.log"
# accesslog = "C:/path/to/access.log"
