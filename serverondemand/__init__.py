from pkg_resources import resource_string

def get_resource(path):
    return resource_string(__name__, path)

