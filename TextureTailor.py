from tkinter import *
from tkinter.filedialog import askdirectory
from tkinter.ttk import *
from tkinter import messagebox
import plistlib
import os
from PIL import Image  # tkinter也有Image, 所以后调用


def check_format(plist):
    fm = plist['metadata']['format']
    items = []
    if fm == 2:
        for key in plist['frames']:
            items.append(transform_v2(plist['frames'][key], key))
    elif fm == 3:
        for key in plist['frames']:
            items.append(transform_v3(plist['frames'][key], key))
    else:
        fail()
    return items


'''
必要属性
1. 切割区域            Rect 
2. 旋转               Rotated
3. 子图原始尺寸       SourceSize
4. 偏移量              Offset


V2
- frames
    name.png
        frame
        sourceSize
        sourceColorRect
        offset
        rotated
- metadata
    format : 2
V3
- frames
    name.png
        textureRect : 父图切割区域            Rect
        spriteSourceSize : 子图整体尺寸       SourceSize
        spriteColorRect ： 子图渲染原点和尺寸  ColorRect
        spriteTrimmed ： 子图渲染原点是否偏移  Trimmed
        spriteOffset ： 渲染原点偏移量        Offset
        textureRotated ： 图片是否旋转         Rotated
        spriteSize
        aliases[]
- metadata
    format : 3
'''


def transform_v2(frame, pathname):
    result = {'pathname': pathname}
    if frame['frame']:
        p1 = frame['frame'].replace('}', '').replace('{', '').split(',')
        p2 = frame['sourceSize'].replace('}', '').replace('{', '').split(',')
        p3 = frame['sourceColorRect'].replace('}', '').replace('{', '').split(',')
        p4 = frame['rotated']

        # 去透明后的子图矩形
        x, y, w, h = tuple(map(int, p1))
        # 子图原始大小
        size = tuple(map(int, p2))
        # 子图在原始图片中的偏移
        ox, oy, _, _ = tuple(map(int, p3))

        # 获取子图左上角，右下角
        if p4:
            box = (x, y, x + h, y + w)
        else:
            box = (x, y, x + w, y + h)
        result['Rect'] = box
        result['SourceSize'] = size
        result['Offset'] = (ox, oy)
        result['Rotated'] = p4
    return result


def transform_v3(frame, pathname):
    result = {'pathname': pathname}
    if 'textureRect' in frame.keys():
        p1 = frame['textureRect'].replace('}', '').replace('{', '').split(',')
        p2 = frame['spriteSourceSize'].replace('}', '').replace('{', '').split(',')
        p3 = frame['spriteOffset'].replace('}', '').replace('{', '').split(',')
        p4 = frame['textureRotated']
    cx = 0
    cy = 0
    if 'spriteTrimmed' in frame.keys():
        if frame['spriteTrimmed']:
            p5 = frame['spriteColorRect'].replace('}', '').replace('{', '').split(',')
            cx, cy, _, _ = tuple(map(int, p5))

    # 去透明后的子图矩形
    x, y, w, h = tuple(map(int, p1))
    # 子图原始大小
    size = tuple(map(int, p2))
    # 子图在原始图片中的偏移
    ox, oy = tuple(map(int, p3))

    # 获取子图左上角，右下角
    if p4:
        box = (x, y, x + h, y + w)
    else:
        box = (x, y, x + w, y + h)

    result['Rect'] = box
    result['SourceSize'] = size
    result['Offset'] = (ox + cx, oy + cy)
    # result['Offset'] = (ox, oy)
    result['Rotated'] = p4
    return result


def export_image(img, path, item):
    box = item['Rect']
    size = item['SourceSize']
    offset = item['Offset']
    rotated = item['Rotated']
    pathname = item['pathname']
    # 使用原始大小创建图像，全透明
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    # 从图集中裁剪出子图
    sprite = img.crop(box)

    # rotated纹理旋转90度
    if rotated:
        sprite = sprite.transpose(Image.ROTATE_90)

    # 粘贴子图，设置偏移
    image.paste(sprite, offset)

    img_path = os.path.join(path, pathname)
    # 保存到文件
    print('保存文件：%s' % img_path)
    image.save(img_path, 'png')


def check_path():
    beginBtn.configure(text="正在分解", state=DISABLED)

    tnames = []
    plists = []
    pngs = []
    for fname in os.listdir(dir_path.get()):
        if os.path.splitext(fname)[1] == '.plist':
            plists.append(os.path.splitext(fname)[0])
        if os.path.splitext(fname)[1] == '.png':
            pngs.append(os.path.splitext(fname)[0])

    for plist in plists:
        for png in pngs:
            if plist == png:
                tnames.append(plist)

    total_count = len(tnames)
    finish_count = 0
    pb["maximum"] = total_count
    pb["value"] = finish_count

    for tname in tnames:
        # 改变工作目录
        os.chdir(dir_path.get())

        plist_name = tname + '.plist'
        print('plist_name:' + plist_name)
        # 使用plistlib库加载 plist 文件
        lp = plistlib.load(open(plist_name, 'rb'))
        # 加载 png 图片文件
        img = Image.open(tname + '.png')
        items = check_format(lp)
        path = os.path.join(dir_path.get(), tname)
        # 检测导出目录
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except Exception as e:
                print(e)
                return

        for item in items:
            export_image(img, path, item)

        finish_count = finish_count + 1
        update_status(finish_count, total_count)
    messagebox.showinfo('分解完成', '请查看' + dir_path.get())
    beginBtn.configure(text="开始分解", state=NORMAL)


def fail():
    messagebox.showerror("执行失败")
    beginBtn.configure(text="开始分解", state=NORMAL)


def seleted_path():
    dir_path.set(askdirectory())
    print("文件夹路径：" + dir_path.get())


def update_status(finish_count, total_count):
    pb["value"] = finish_count
    status_str.set("{} / {}".format(finish_count, total_count))
    root.update()  # 更新画面


if __name__ == '__main__':
    root = Tk()
    root.title("TextureTailor")

    dir_path = StringVar()  # 源文件目录
    status_str = StringVar()  # 执行进度 完成个数 / 总个数

    # 目录选择
    Label(root, text="文件目录:").grid(row=0, column=0)

    Entry(root, textvariable=dir_path).grid(row=0, column=1)
    Button(root, text="选择目录", command=seleted_path).grid(row=0, column=2)
    # 执行按钮
    beginBtn = Button(root, text="开始分解", command=check_path)
    beginBtn.grid(row=1)

    # 使用默认设置创建进度条
    pb = Progressbar(root, length=200, mode="determinate", orient=HORIZONTAL)
    pb.grid(row=2, column=1)
    # 进度
    Label(root, textvariable=status_str).grid(row=2, column=2)

    root.mainloop()
