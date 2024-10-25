import tkinter as tk
from tkinter import filedialog, messagebox
import os
import requests
import json
import rarfile
import base64

class ModInstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("750x450")  
        self.center_window()
        self.root.title("V.A Proxy Speedrun Mod Installer")

        self.mods = self.load_mod_list()
        self.plugins_path = self.load_plugins_path()
        self.create_widgets()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def get_script_directory(self):
        return os.path.dirname(os.path.abspath(__file__))

    def load_mod_list(self):
        url = "https://api.github.com/repos/vainstar1/vap-mod-links/contents/mods.txt"
        try:
            response = requests.get(url)
            response.raise_for_status()  
            content = response.json()
            
            mods_text = base64.b64decode(content['content']).decode('utf-8')
            lines = mods_text.strip().splitlines()
            
            mods_dict = {"Speedrunning Mods": [], "Optional Mods": [], "Splits": []}
            for line in lines:
                if line.startswith("#") or not line.strip(): 
                    continue
                name, link, category = line.split(",", 2) 
                category = category.strip()  
                if category == "Splits":
                    mods_dict["Splits"].append({"name": name.strip(), "url": link.strip()})
                else:
                    mods_dict[category + " Mods"].append({"name": name.strip(), "url": link.strip()})
            
            return mods_dict
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load mod links: {e}")
            return {"Speedrunning Mods": [], "Optional Mods": [], "Splits": []}

    def create_widgets(self):
        self.path_label = tk.Label(self.root, text="V.A Proxy Root Folder:")
        self.path_label.pack(pady=5)

        self.path_entry = tk.Entry(self.root, width=50)
        self.path_entry.pack(pady=5)
        self.path_entry.insert(0, self.plugins_path)

        self.browse_button = tk.Button(self.root, text="Browse", command=self.browse_folder)
        self.browse_button.pack(pady=5)

        self.bepinex_button = tk.Button(self.root, text="Install BepInEx", command=self.install_bepinex)
        self.bepinex_button.pack(pady=5)

        self.check_vars = {}
        self.installed_mods = self.get_installed_mods()

        self.create_mod_section("Speedrunning Mods", True)

        self.create_splits_section()

        self.create_mod_section("Optional Mods", False)

        self.install_button = tk.Button(self.root, text="Install Selected Mods", command=self.install_mods)
        self.install_button.pack(pady=10)

        self.progress_label = tk.Label(self.root, text=" ", font=("Arial", 10))
        self.progress_label.pack(pady=5)

        self.adjust_window_size()

    def adjust_window_size(self):
        mod_count = sum(len(mods) for mods in self.mods.values())

        estimated_height = 550 + (mod_count * 15)  

        max_height = 800
        estimated_height = min(estimated_height, max_height)

        self.root.geometry(f"750x{estimated_height}")
        self.center_window()  

    def create_mod_section(self, category, is_speedrunning):
        category_label = tk.Label(self.root, text=category, font=("Arial", 12, "bold"))
        category_label.pack(pady=5)
        for mod in self.mods[category]:
            var = tk.BooleanVar(value=False) 
            if mod["name"] in self.installed_mods and not is_speedrunning:
                var.set(False)  
            self.check_vars[mod["name"]] = var
            check_button = tk.Checkbutton(self.root, text=mod["name"], variable=var)
            check_button.pack(anchor="w")

    def create_splits_section(self):
        self.splits_label = tk.Label(self.root, text="Install Splits", font=("Arial", 12, "bold"))
        self.splits_label.pack(pady=5)

        self.split_check_vars = {}
        for split in self.mods["Splits"]:
            var = tk.BooleanVar(value=False)
            self.split_check_vars[split["name"]] = var
            split_checkbutton = tk.Checkbutton(self.root, text=split["name"], variable=var)
            split_checkbutton.pack(anchor="w")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
            self.save_plugins_path(folder)

    def install_bepinex(self):
        root_path = self.path_entry.get()
        if not os.path.isdir(root_path):
            messagebox.showerror("Error", "Invalid V.A Proxy root folder path.")
            return
        bepinex_path = os.path.join(root_path, "BepInEx")
        if os.path.exists(bepinex_path):
            if not os.path.exists(os.path.join(bepinex_path, "plugins")):
                messagebox.showerror("BepInEx Initialization", "BepInEx is installed, but the 'plugins' folder is missing. Please run V.A Proxy once to initialize the folder.")
            else:
                messagebox.showinfo("BepInEx Installation", "BepInEx is already installed and initialized!")
        else:
            try:
                with rarfile.RarFile("BepInExPack.rar") as rar_ref:
                    rar_ref.extractall(root_path)
                messagebox.showinfo("BepInEx Installation", "BepInEx successfully installed! Run V.A Proxy to initialize your Plugins folder.")
            except rarfile.Error as e:
                messagebox.showerror("Error", f"Failed to extract BepInExPack.rar: {e}")

    def install_mods(self):
        root_path = self.path_entry.get()
        plugins_path = os.path.join(root_path, "BepInEx", "plugins")
        if not os.path.isdir(plugins_path):
            messagebox.showerror("Error", "BepInEx is installed, but the 'plugins' folder is missing. Please run V.A Proxy once to initialize the folder.")
            return
        self.save_plugins_path(root_path)

        selected_mods = [mod for mod, var in self.check_vars.items() if var.get()]
        selected_splits = [split for split, var in self.split_check_vars.items() if var.get()]

        if not selected_mods and not selected_splits:
            messagebox.showinfo("No mods or splits selected", "Please select at least one mod or split to install.")
            return

        self.progress_label.config(text="")  
        total_items = len(selected_mods) + len(selected_splits)
        current_item = 0

        self.progress_label.config(text=f"Installing Mods ({current_item}/{total_items})")  
        for mod_name in selected_mods:
            current_item += 1
            self.root.update_idletasks()  
            if mod_name not in self.installed_mods:
                mod_url = self.get_mod_url(mod_name)
                if mod_url:
                    self.download_and_install_mod(mod_url, plugins_path)
            
            self.progress_label.config(text=f"Installing Mods ({current_item}/{total_items})")

        if selected_splits:
            for split_name in selected_splits:
                current_item += 1
                self.root.update_idletasks() 
                split_url = self.get_mod_url(split_name)
                if split_url:
                    self.download_and_install_split(split_url, f"{split_name}.json", plugins_path)
            
                self.progress_label.config(text=f"Installing Mods ({current_item}/{total_items})")

        self.progress_label.config(text="Installation completed successfully!")
        messagebox.showinfo("Success", "Selected mods and splits installed successfully.")
        
        self.root.after(1000, lambda: self.progress_label.config(text=""))

    def get_installed_mods(self):
        root_path = self.path_entry.get()
        plugins_path = os.path.join(root_path, "BepInEx", "plugins")
        installed_mods = []
        if os.path.isdir(plugins_path):
            installed_mods = [f[:-4] for f in os.listdir(plugins_path) if f.endswith('.dll')]
        return installed_mods

    def get_mod_url(self, mod_name):
        for mods in self.mods.values():
            for mod in mods:
                if mod["name"] == mod_name:
                    if mod_name in ["Any%", "All Bosses"]: 
                        return mod["url"]

                    try:
                        response = requests.get(mod["url"])
                        if response.status_code == 200:
                            data = response.json()
                            if data:
                                latest_release = data[0]
                                if 'assets' in latest_release:
                                    for asset in latest_release['assets']:
                                        if asset['name'].endswith('.dll'):
                                            return asset['browser_download_url']
                                else:
                                    print(f"'assets' key missing in the release data for mod: {mod_name}")
                                    messagebox.showerror("Error", f"No assets available for mod: {mod_name}")
                        else:
                            print(f"Failed to fetch mod release for: {mod_name}")
                    except Exception as e:
                        print(f"Error fetching release data for {mod_name}: {e}")
        return None

    def download_and_install_mod(self, mod_url, plugins_path):
        try:
            response = requests.get(mod_url)
            if response.status_code == 200:
                mod_filename = os.path.basename(mod_url)
                mod_path = os.path.join(plugins_path, mod_filename)
                with open(mod_path, 'wb') as mod_file:
                    mod_file.write(response.content)
            else:
                print(f"Failed to download mod: {mod_url}")
        except Exception as e:
            print(f"Error downloading mod: {e}")

    def download_and_install_split(self, split_url, split_filename, plugins_path):
        try:
            response = requests.get(split_url)
            if response.status_code == 200:
                split_path = os.path.join(plugins_path, "SpeedrunningUtils.Splits", split_filename)
                os.makedirs(os.path.dirname(split_path), exist_ok=True)  
                with open(split_path, 'wb') as split_file:
                    split_file.write(response.content)
            else:
                print(f"Failed to download split: {split_url}")
        except Exception as e:
            print(f"Error downloading split: {e}")

    def load_plugins_path(self):
        plugins_path_file = os.path.join(self.get_script_directory(), "plugins_path.txt")
        if not os.path.exists(plugins_path_file):
            with open(plugins_path_file, "w") as file:
                file.write("") 
        with open(plugins_path_file, "r") as file:
            return file.read().strip()

    def save_plugins_path(self, path):
        plugins_path_file = os.path.join(self.get_script_directory(), "plugins_path.txt")
        with open(plugins_path_file, "w") as file:
            file.write(path)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModInstallerApp(root)
    root.mainloop()
