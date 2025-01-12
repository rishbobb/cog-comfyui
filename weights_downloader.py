import subprocess
import time
import os
import json

from weights_manifest import WeightsManifest

BASE_URL = "https://weights.replicate.delivery/default/comfy-ui"


class WeightsDownloader:
    def __init__(self):
        self.weights_manifest = WeightsManifest()
        self.weights_map = self.weights_manifest.weights_map
        self.append_custom_models_from_file()

    def append_custom_models_from_file(self):
        with open("extra_weights.json", "r") as f:
            custom = json.load(f)
        for key in custom:
            self.weights_map[key] = custom[key]
        print("Appended static custom models")
    
    def append_custom_models_from_string(self, models):
        custom = json.loads(models)
        for key in custom:
            obj = custom[key]
            obj["notar"] = True
            self.weights_map[key] = obj
            print(f"Added extra model: {key}")
        print("Appended dynamic custom models")

    def download_weights(self, weight_str):
        if weight_str in self.weights_map:
            if self.weights_manifest.is_non_commercial_only(weight_str):
                print(
                    f"⚠️  {weight_str} is for non-commercial use only. Unless you have obtained a commercial license.\nDetails: https://github.com/fofr/cog-comfyui/blob/main/weights_licenses.md"
                )
            self.download_if_not_exists(
                weight_str,
                self.weights_map[weight_str]["url"],
                self.weights_map[weight_str]["dest"],
            )
            print(self.weights_map[weight_str]["url"])
            print(self.weights_map[weight_str]["dest"])
        else:
            raise ValueError(
                f"{weight_str} unavailable. View the list of available weights: https://github.com/fofr/cog-comfyui/blob/main/supported_weights.md"
            )

    def download_torch_checkpoints(self):
        self.download_if_not_exists(
            "mobilenet_v2-b0353104.pth",
            f"{BASE_URL}/custom_nodes/comfyui_controlnet_aux/mobilenet_v2-b0353104.pth.tar",
            "/root/.cache/torch/hub/checkpoints/",
        )

    def download_if_not_exists(self, weight_str, url, dest):
        if not os.path.exists(f"{dest}/{weight_str}"):
            self.download(weight_str, url, dest)

    def download(self, weight_str, url, dest):
        if "/" in weight_str:
            subfolder = weight_str.rsplit("/", 1)[0]
            dest = os.path.join(dest, subfolder)
            os.makedirs(dest, exist_ok=True)

        print(f"⏳ Downloading {weight_str} to {dest}")
        tar = True
        try:
            if self.weights_map[weight_str]["notar"]:
                tar = False
        except:
            pass
        start = time.time()
        if tar:
            subprocess.check_call(
                ["pget", "--log-level", "warn", "-xf", url, dest], close_fds=False
            )
        else:
            try:
                subprocess.check_call(["mkdir", f"{dest}"])
            except:
                pass
            subprocess.check_call(
                ["pget", "--log-level", "warn", url, f"{dest}/{weight_str}"], close_fds=False
            )
        elapsed_time = time.time() - start
        try:
            file_size_bytes = os.path.getsize(
                os.path.join(dest, os.path.basename(weight_str))
            )
            file_size_megabytes = file_size_bytes / (1024 * 1024)
            print(
                f"⌛️ Downloaded {weight_str} in {elapsed_time:.2f}s, size: {file_size_megabytes:.2f}MB"
            )
        except FileNotFoundError:
            print(f"Warning: Could not get the file size for {weight_str}")
