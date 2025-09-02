# JupyterLab Server Configuration
c = get_config()

# SECURITY: Enable authentication - CRITICAL FIX
import os
c.ServerApp.token = os.environ.get('JUPYTER_TOKEN', 'CHANGE_THIS_SECURE_TOKEN')
c.ServerApp.password = os.environ.get('JUPYTER_PASSWORD', 'CHANGE_THIS_SECURE_PASSWORD')
c.ServerApp.password_required = True

# Restrict to localhost only for security
c.ServerApp.ip = '127.0.0.1'

# Enable JupyterLab
c.ServerApp.default_url = '/lab'

# Security: Restrict origins and remote access
c.ServerApp.allow_origin = 'http://localhost:8888'
c.ServerApp.allow_remote_access = False
