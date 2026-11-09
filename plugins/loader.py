import os, importlib.util

class PluginLoader:
    def __init__(self, folder=None):
        self.folder = folder or os.path.dirname(os.path.abspath(__file__))
        self.plugins = {}

    def load_all(self):
        self.plugins = {}
        for name in sorted(os.listdir(self.folder)):
            if not name.endswith(".py") or name.startswith("_") or name == "loader.py":
                continue
            path = os.path.join(self.folder, name)
            mod_name = "plugin_" + name[:-3]
            try:
                spec = importlib.util.spec_from_file_location(mod_name, path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                info = getattr(mod, "PLUGIN_INFO", {"name": name[:-3], "version": "?"})
                self.plugins[mod_name] = {"info": info, "module": mod}
            except Exception as e:
                self.plugins[mod_name] = {"info": {"name": name, "error": str(e)}, "module": None}
        return self.plugins

    def list_info(self):
        return {k: v["info"] for k, v in self.plugins.items()}
