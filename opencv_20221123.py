import cv2    # 调用opencv包
img = cv2.imread(r'C:\Users\chenzhanchao\Desktop\af0f2ffe69ae48459d299ddb2b255e33.png')   #读取图像位置
cv2.namedWindow("demo")                                  #对显示图像的窗口进行命名
#cv2.imshow("demo", img)                                  #显示图像

#cv2.resizeWindow("windowname", width, height)
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)          #对图像进行灰度处理
data = cv2.resize(img_gray, dsize = None, fx = 0.3, fy = 0.3,interpolation = cv2.INTER_LINEAR)  #将显示的图像宽和高都变为一半

cv2.imshow("demo", data)
cv2.waitKey(delay = 0)
print(img.shape) #显示图像的类型以及分辨率

print(img)