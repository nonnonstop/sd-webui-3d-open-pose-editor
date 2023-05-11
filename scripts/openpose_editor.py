import html
import json
import os.path
import pathlib
from typing import Optional, Dict
import urllib.parse

import gradio as gr

try:
    root_path = pathlib.Path(__file__).resolve().parents[1]
except NameError:
    import inspect

    root_path = pathlib.Path(inspect.getfile(lambda: None)).resolve().parents[1]


def get_asset_url(
    file_path: pathlib.Path, append: Optional[Dict[str, str]] = None
) -> str:
    if append is None:
        append = {"v": str(os.path.getmtime(file_path))}
    else:
        append = append.copy()
        append["v"] = str(os.path.getmtime(file_path))
    return f"/file={file_path.absolute()}?{urllib.parse.urlencode(append)}"


def write_config_file() -> pathlib.Path:
    assets = {
        "models/hand.fbx": get_asset_url(root_path / "models" / "hand.fbx"),
        "models/foot.fbx": get_asset_url(root_path / "models" / "foot.fbx"),
        "src/poses/data.bin": get_asset_url(root_path / "src" / "poses" / "data.bin"),
    }

    MEDIAPIPE_POSE_VERSION = "0.5.1675469404"
    mediapipe_dir = root_path / "downloads" / "pose" / MEDIAPIPE_POSE_VERSION
    for file_name in [
        "pose_landmark_full.tflite",
        "pose_web.binarypb",
        "pose_solution_packed_assets.data",
        "pose_solution_simd_wasm_bin.wasm",
        "pose_solution_packed_assets_loader.js",
        "pose_solution_simd_wasm_bin.js",
    ]:
        file_path = mediapipe_dir / file_name
        if not file_path.exists():
            continue
        assets[file_name] = get_asset_url(file_path.absolute())

    consts = {"assets": assets}

    config_dir = root_path / "downloads"
    config_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
    config_path = config_dir / "config.json"
    config_path.write_text(json.dumps(consts))
    return config_path


def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as blocks:
        create_ui()
    return [(blocks, "3D Openpose", "threedopenpose")]


def create_ui():
    try:
        from modules.shared import opts

        cn_max: int = opts.control_net_max_models_num
        use_online: bool = opts.openpose3d_use_online_version
    except (ImportError, AttributeError):
        cn_max = 0
        use_online = False

    if use_online:
        html_url = "https://zhuyu1997.github.io/open-pose-editor/"
    else:
        config = {"config": get_asset_url(write_config_file()) or ""}
        html_url = get_asset_url(root_path / "pages" / "index.html", config)

    with gr.Tabs(elem_id="openpose3d_main"):
        with gr.Tab(label="Edit Openpose"):
            gr.HTML(
                f"""
                <iframe id="openpose3d_iframe" src="{html.escape(html_url)}"></iframe>
                """
            )
            gr.Markdown(
                "Original: [Online 3D Openpose Editor](https://zhuyu1997.github.io/open-pose-editor/)"
            )
        with gr.Tab(label="Send to ControlNet"):
            with gr.Row():
                send_t2i = gr.Button(value="Send to txt2img", variant="primary")
                send_i2i = gr.Button(value="Send to img2img", variant="primary")
            with gr.Row():
                cn_dropdown_list = [str(i) for i in range(cn_max)]
                cn_dropdown_list.insert(0, "-")
                with gr.Column(variant="panel"):
                    pose_image = gr.Image(
                        label="Pose",
                        elem_id="openpose3d_pose_image",
                    )
                    with gr.Row():
                        pose_target = gr.Dropdown(
                            label="Control Model number",
                            choices=cn_dropdown_list,
                            value="0" if cn_max >= 1 else "-",
                        )
                        pose_download = gr.Button(value="Download")
                with gr.Column(variant="panel"):
                    depth_image = gr.Image(
                        label="Depth",
                        elem_id="openpose3d_depth_image",
                    )
                    with gr.Row():
                        depth_target = gr.Dropdown(
                            label="Control Model number",
                            choices=cn_dropdown_list,
                            value="1" if cn_max >= 2 else "-",
                        )
                        depth_download = gr.Button(value="Download")
                with gr.Column(variant="panel"):
                    normal_image = gr.Image(
                        label="Normal",
                        elem_id="openpose3d_normal_image",
                    )
                    with gr.Row():
                        normal_target = gr.Dropdown(
                            label="Control Model number",
                            choices=cn_dropdown_list,
                            value="2" if cn_max >= 3 else "-",
                        )
                        normal_download = gr.Button(value="Download")
                with gr.Column(variant="panel"):
                    canny_image = gr.Image(
                        label="Canny",
                        elem_id="openpose3d_canny_image",
                    )
                    with gr.Row():
                        canny_target = gr.Dropdown(
                            label="Control Model number",
                            choices=cn_dropdown_list,
                            value="3" if cn_max >= 4 else "-",
                        )
                        canny_download = gr.Button(value="Download")

    send_cn_inputs = [
        pose_image,
        pose_target,
        depth_image,
        depth_target,
        normal_image,
        normal_target,
        canny_image,
        canny_target,
    ]
    send_t2i.click(
        None,
        send_cn_inputs,
        None,
        _js="window.openpose3d.sendTxt2img",
    )
    send_i2i.click(
        None,
        send_cn_inputs,
        None,
        _js="window.openpose3d.sendImg2img",
    )
    pose_download.click(
        None,
        pose_image,
        None,
        _js="(v) => window.openpose3d.downloadImage(v, 'pose')",
    )
    depth_download.click(
        None,
        depth_image,
        None,
        _js="(v) => window.openpose3d.downloadImage(v, 'depth')",
    )
    normal_download.click(
        None,
        normal_image,
        None,
        _js="(v) => window.openpose3d.downloadImage(v, 'normal')",
    )
    canny_download.click(
        None,
        canny_image,
        None,
        _js="(v) => window.openpose3d.downloadImage(v, 'canny')",
    )


def on_ui_settings():
    from modules.shared import OptionInfo, opts

    section = ("openpose3d", "3D Openpose Editor")

    opts.add_option(
        "openpose3d_use_online_version",
        OptionInfo(False, "Use online version", section=section),
    )


def main():
    js_path = root_path / "javascript" / "index.js"
    css_path = root_path / "style.css"

    original_template_response = gr.routes.templates.TemplateResponse
    head = """
    <script>
        function waitForElement(parent, selector) {
            return new Promise((resolve) => {
                const observer = new MutationObserver(() => {
                    if (!parent.querySelector(selector)) {
                        return
                    }
                    observer.disconnect()
                    resolve(undefined)
                })

                observer.observe(parent, {
                    childList: true,
                    subtree: true,
                })

                if (parent.querySelector(selector)) {
                    resolve(undefined)
                }
            })
        }
        let onTabChangedCallback
        function gradioApp() {
            const elems = document.getElementsByTagName('gradio-app')
            const gradioShadowRoot = elems.length == 0 ? null : elems[0].shadowRoot
            return gradioShadowRoot ? gradioShadowRoot : document
        }
        async function onUiLoaded(callback){
            await waitForElement(gradioApp(), '#openpose3d_main')
            await callback()
            await onTabChangedCallback?.()
        }
        function onUiUpdate(callback){
            onTabChangedCallback = callback
        }
    </script>
    """
    head += f"""
    <script type="module">
        document.addEventListener("DOMContentLoaded", function() {{import("{get_asset_url(js_path)}")}})
    </script>
    """

    def template_response(*args, **kwargs):
        res = original_template_response(*args, **kwargs)
        res.body = res.body.replace(b"</head>", f"{head}</head>".encode("utf8"))
        res.init_headers()
        return res

    gr.routes.templates.TemplateResponse = template_response

    with gr.Blocks(analytics_enabled=False, css=css_path.read_text()) as blocks:
        with gr.Tab(label="3D Openpose", elem_id="tab_threedopenpose"):
            create_ui()
    blocks.launch()


try:
    from modules import script_callbacks

    script_callbacks.on_ui_tabs(on_ui_tabs)
    script_callbacks.on_ui_settings(on_ui_settings)
except ImportError:
    main()
