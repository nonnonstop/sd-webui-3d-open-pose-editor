import { getCurrentTime } from '../../utils/time'
import { download } from '../../utils/transfer'
import {
    openGradioAccordion,
    switchGradioTab,
    updateGradioImage,
    waitForElementToBeInDocument,
    waitForElementToBeRemoved,
} from './internal/gradio'
import {
    AddMessageEventListener,
    InitMessageListener,
    InvokeCommand,
} from './internal/message'

const isTabActive = () => {
    const tab = gradioApp().querySelector<HTMLElement>('#tab_threedopenpose')
    return tab && tab.style.display != 'none'
}

let isInitialized = false
let isPaused = false

onUiLoaded(async () => {
    console.log('sd-webui-3d-open-pose-editor: onUiLoaded')

    const sendToControlNet = async (
        container: Element,
        poseImage: string | null,
        poseTarget: string,
        depthImage: string | null,
        depthTarget: string,
        normalImage: string | null,
        normalTarget: string,
        cannyImage: string | null,
        cannyTarget: string
    ) => {
        let element: Element | null | undefined =
            container.querySelector('#controlnet')
        if (!element) {
            for (const spans of container.querySelectorAll<HTMLSpanElement>(
                '.cursor-pointer > span'
            )) {
                if (!spans.textContent?.includes('ControlNet')) {
                    continue
                }
                if (spans.textContent?.includes('M2M')) {
                    continue
                }
                element = spans.parentElement?.parentElement
            }
            if (!element) {
                console.error('ControlNet element not found')
                return
            }
        } else {
            openGradioAccordion(element)
        }
        const tabSelector = '#txt2img_controlnet_tabs > div.gradio-tabitem'
        await waitForElementToBeInDocument(element, tabSelector);
        const imageElems = element.querySelectorAll(tabSelector);
        const tabsElem = element.querySelector('.tab-nav')
        if (poseImage && poseTarget != '' && poseTarget != '-') {
            const tabIndex = Number(poseTarget)
            if (tabsElem) {
                switchGradioTab(tabsElem, tabIndex)
            }
            await updateGradioImage(imageElems[tabIndex], poseImage, 'pose.png')
        }
        if (depthImage && depthTarget != '' && depthTarget != '-') {
            const tabIndex = Number(depthTarget)
            if (tabsElem) {
                switchGradioTab(tabsElem, tabIndex)
            }
            await updateGradioImage(
                imageElems[tabIndex],
                depthImage,
                'depth.png'
            )
        }
        if (normalImage && normalTarget != '' && normalTarget != '-') {
            const tabIndex = Number(normalTarget)
            if (tabsElem) {
                switchGradioTab(tabsElem, tabIndex)
            }
            await updateGradioImage(
                imageElems[tabIndex],
                normalImage,
                'normal.png'
            )
        }
        if (cannyImage && cannyTarget != '' && cannyTarget != '-') {
            const tabIndex = Number(cannyTarget)
            if (tabsElem) {
                switchGradioTab(tabsElem, tabIndex)
            }
            await updateGradioImage(
                imageElems[tabIndex],
                cannyImage,
                'canny.png'
            )
        }
    }

    window.openpose3d = {
        sendTxt2img: async (
            poseImage: string | null,
            poseTarget: string,
            depthImage: string | null,
            depthTarget: string,
            normalImage: string | null,
            normalTarget: string,
            cannyImage: string | null,
            cannyTarget: string
        ) => {
            const container = gradioApp().querySelector(
                '#txt2img_script_container'
            )!
            switch_to_txt2img()
            await sendToControlNet(
                container,
                poseImage,
                poseTarget,
                depthImage,
                depthTarget,
                normalImage,
                normalTarget,
                cannyImage,
                cannyTarget
            )
        },
        sendImg2img: async (
            poseImage: string,
            poseTarget: string,
            depthImage: string,
            depthTarget: string,
            normalImage: string,
            normalTarget: string,
            cannyImage: string,
            cannyTarget: string
        ) => {
            const container = gradioApp().querySelector(
                '#img2img_script_container'
            )!
            switch_to_img2img()
            await sendToControlNet(
                container,
                poseImage,
                poseTarget,
                depthImage,
                depthTarget,
                normalImage,
                normalTarget,
                cannyImage,
                cannyTarget
            )
        },
        downloadImage: (image: string | null, name: string) => {
            if (!image) {
                return
            }
            const fileName = name + '_' + getCurrentTime() + '.png'
            download(image, fileName)
        },
    }

    InitMessageListener()
    AddMessageEventListener({
        MakeImages: async (args: Record<string, string>) => {
            for (const [name, url] of Object.entries(args)) {
                const element = gradioApp().querySelector(
                    `#openpose3d_${name}_image`
                )!
                const updateImage = async (
                    element: Element,
                    url: string,
                    name: string
                ) => {
                    const blob = await (await fetch(url)).blob()
                    const file = new File([blob], name)
                    const dt = new DataTransfer()
                    dt.items.add(file)
                
                    element
                        .querySelector<HTMLButtonElement>("button[aria-label='Clear']")
                        ?.click()
                    await waitForElementToBeRemoved(element, "button[aria-label='Clear']")
                    const input = element.querySelector<HTMLInputElement>("input[type='file']")!
                    input.value = ''
                    input.files = dt.files
                    input.dispatchEvent(
                        new Event('change', {
                            bubbles: true,
                            composed: true,
                        })
                    )
                    await waitForElementToBeInDocument(element, "button[aria-label='Clear']")
                }
                await updateImage(element, url, name + '.png')
            }
            const tabs = gradioApp().querySelector('#openpose3d_main')!
            switchGradioTab(tabs, 1)
        },
    })

    for (let i = 0; i < 30; ++i) {
        try {
            await InvokeCommand('GetAppVersion')
            isInitialized = true
            break
        } catch (error: any) {
            if (error.status != 'Timeout') {
                throw error
            }
        }
    }
    if (!isInitialized) {
        console.error('sd-webui-3d-open-pose-editor: Timeout')
        return
    }

    // await InvokeCommand('OutputWidth', 512)
    // await InvokeCommand('OutputHeight', 512)
    if (!isTabActive()) {
        await InvokeCommand('Pause')
    }
})

onUiUpdate(async () => {
    if (!isInitialized) {
        return
    }
    if (isTabActive()) {
        if (isPaused) {
            isPaused = false
            await InvokeCommand('Resume')
        }
    } else {
        if (!isPaused) {
            isPaused = true
            await InvokeCommand('Pause')
        }
    }
})
