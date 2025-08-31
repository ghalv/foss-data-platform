# JupyterLab Server Configuration
c = get_config()

# Disable authentication completely for development
c.ServerApp.token = ''
c.ServerApp.password = ''
c.ServerApp.token_generator = None
c.ServerApp.password_required = False

# Allow all IPs
c.ServerApp.ip = '0.0.0.0'

# Enable JupyterLab
c.ServerApp.default_url = '/lab'

# Disable security warnings for development
c.ServerApp.allow_origin = '*'
c.ServerApp.allow_remote_access = True
