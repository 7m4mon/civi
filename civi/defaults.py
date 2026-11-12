"""Device factory names, independent of saved user/acquired discovery names."""
DEFAULT_HOSTNAME = 'civi'


def default_description(config):
    return f'CIVI {config["serial_number"]}'
