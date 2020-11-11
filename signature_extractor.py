import cv2
import matplotlib.pyplot as plt
from skimage import measure, morphology
from skimage.color import label2rgb
from skimage.measure import regionprops
import numpy as np
import pytesseract
import uuid

# read the input image
from pdf2image import convert_from_path


def get_signatures(pdf_images,language = None):
    # pdf_images = convert_from_path('./inputs_pdf/in{}.pdf'.format(num))
    # or_img = cv2.imread('./inputs/in{}.jpg'.format(num))
    or_img = np.array(pdf_images[0])

    img_rgb = cv2.cvtColor(or_img, cv2.COLOR_BGR2RGB)
    text =  pytesseract.image_to_string(img_rgb, lang=language)

    gray = cv2.cvtColor(or_img, cv2.COLOR_BGR2GRAY)
    img = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_MEAN_C,\
                cv2.THRESH_BINARY,11,2)

    img = cv2.threshold(img, 10, 255, cv2.THRESH_BINARY)[1]  # ensure binary

    # connected component analysis by scikit-learn framework
    blobs = img > img.mean()
    blobs_labels = measure.label(blobs, background=1)
    image_label_overlay = label2rgb(blobs_labels, image=img)

    fig, ax = plt.subplots(figsize=(10, 6))

    '''
    # plot the connected components (for debugging)
    ax.imshow(image_label_overlay)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()
    '''

    the_biggest_component = 0
    total_area = 0
    counter = 0
    average = 0.0
    for region in regionprops(blobs_labels):
        if (region.area > 10):
            total_area = total_area + region.area
            counter = counter + 1
        # print region.area # (for debugging)
        # take regions with large enough areas
        if (region.area >= 250):
            if (region.area > the_biggest_component):
                the_biggest_component = region.area

    average = (total_area/counter)
    # print("the_biggest_component: " + str(the_biggest_component))
    # print("average: " + str(average))

    # experimental-based ratio calculation, modify it for your cases
    # a4_constant is used as a threshold value to remove connected pixels
    # are smaller than a4_constant for A4 size scanned documents
    a4_constant = ((average/84.0)*250.0) + 1200
    # print("a4_constant: " + str(a4_constant))

    # remove the connected pixels are smaller than a4_constant
    b = morphology.remove_small_objects(blobs_labels, a4_constant)
    # save the the pre-version which is the image is labelled with colors
    # as considering connected components
    # plt.imsave('pre_version.png', b)

    # read the pre-version
    # img = cv2.imread('pre_version.png', 0)
    # ensure binary
    # img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    # save the the result
    b = (255 - b)
    image = np.uint8(b)
    # img = img.astype('uint8')
    # img = cv2.UMat(b)
    # print(type(img))
    cv2.threshold(image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU,image_label_overlay)
    cv2.bitwise_not(image,image)
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
    image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, rect_kernel)
    contours, hier = cv2.findContours(image, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)

    links = []
    if len(contours) != 0:
        for c in contours:
            filename = str(uuid.uuid4())
            x,y,w,h = cv2.boundingRect(c)
            # print(np.sum(cv2.threshold(gray[y:y+h,x:x+w-1], 127, 255, cv2.THRESH_BINARY)[1]  )/gray[y:y+h,x:x+w-1].size)
            thrsh = np.sum(cv2.threshold(gray[y:y+h,x:x+w-1], 127, 255, cv2.THRESH_BINARY)[1]  )/gray[y:y+h,x:x+w-1].size
            print(thrsh,h,w)
            if(h > 30 and w > 30  and h < 700 and w < 700 and  thrsh > 210):
                print("{}.jpg".format(filename))
                # print(np.sum(img[y:y+h,x:x+w-1])/img[y:y+h,x:x+w-1].size)
                # print(np.sum(cv2.threshold(gray[y:y+h,x:x+w-1], 127, 255, cv2.THRESH_BINARY)[1]  )/img[y:y+h,x:x+w-1].size)
                cv2.rectangle(or_img,(x,y),(x+w,y+h),(0,255,0),1)
                cv2.imwrite("./outputs/{}.jpg".format(filename), or_img[y:y+h,x:x+w-1])
                links.append("{}.jpg".format(filename))
    return text,links
# cv2.imwrite("./outputs/output{}.png".format(num), or_img)
