import imutils
import cv2

image = cv2.imread("selfie.jpg")
(height, width, depth) = image.shape
print("width={}, height={} depth={}".format(width, height, depth))

# cv2.imshow("Selfie", image)
# cv2.waitKey(0) 

(B, G, R) = image[100, 500]
print("R={}, G={}, B={}".format(R, G, B))

regionInterest = image[210: 699, 697:1118]
# cv2.imshow("Region of Interest", regionInterest)
# cv2.waitKey(0)

resizedImage = cv2.resize(image, (200, 200))
# cv2.imshow("Resized Image", resizedImage)
# cv2.waitKey(0)

ratio = 300 / width
dimension = (300, int(height * ratio))
aspectRatioResizedImage = cv2.resize(image, dimension)
# cv2.imshow("Aspect Ratio Resized Image", aspectRatioResizedImage)
# cv2.waitKey(0)

imutilsResizedImage = imutils.resize(image, width=300)
# cv2.imshow("Imutils Resized Image", imutilsResizedImage)
# cv2.waitKey(0)

center = (width // 2, height // 2)
matrix = cv2.getRotationMatrix2D(center, -45, 1.0)
rotatedImage = cv2.warpAffine(image, matrix, (width, height))
# cv2.imshow("OpenCV Rotated Image", rotatedImage)
# cv2.waitKey(0)

imutilsRotatedImage = imutils.rotate(image, -45)
# cv2.imshow("Imutils Rotated Image", imutilsRotatedImage)
# cv2.waitKey(0)

imutilsRotatedImage = imutils.rotate_bound(image, 45)
# cv2.imshow("Imutils Rotated & Bounded Image", imutilsRotatedImage)
# cv2.waitKey(0)

blurredImage = cv2.GaussianBlur(image, (11, 11), 0)
# cv2.imshow("Gaussian Blurred Image", blurredImage)
# cv2.waitKey(0)

output = image.copy()
cv2.rectangle(output, (699, 210), (1118, 697), (0, 0, 255), 2)
# cv2.imshow("Rectangle", output)
# cv2.waitKey(0)

output = image.copy()
cv2.circle(output, (300, 150), 20, (255, 0, 0), -1)
# cv2.imshow("Circle", output)
# cv2.waitKey(0)

output = image.copy()
cv2.line(output, (60, 20), (1000, 600), (0, 0, 255), 5)
# cv2.imshow("Line", output)
# cv2.waitKey(0)

output = image.copy()
cv2.putText(output, "OpenCV - Ayudantía Ayudantía de extensión y vinculación de microcontroladores", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 6)
cv2.imshow("Text", output)
cv2.waitKey(0)