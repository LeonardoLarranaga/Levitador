import argparse
import imutils
import cv2

argumentParser = argparse.ArgumentParser()
argumentParser.add_argument("-i", "--image", required=True, help="Path to image")
arguments = vars(argumentParser.parse_args())

image = cv2.imread(arguments["image"])
# cv2.imshow("Image", image)
# cv2.waitKey(0)

grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# cv2.imshow("Gray Image", grayImage)
# cv2.waitKey(0)

edgedImage = cv2.Canny(grayImage, 100, 200)
# cv2.imshow("Edged Image", edgedImage)
# cv2.waitKey(0)

blurredImage = cv2.GaussianBlur(grayImage, (15, 15), 5)
thresholdImage = cv2.threshold(blurredImage, 230, 255, cv2.THRESH_BINARY_INV)[1]
# cv2.imshow("Threshold Image", thresholdImage)
# cv2.waitKey(0)

contours = cv2.findContours(thresholdImage.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = imutils.grab_contours(contours)
output = image.copy()

for contour in contours:
    cv2.drawContours(output, [contour], -1, (240, 0, 159), 3)
# cv2.imshow("Countours", output)
# cv2.waitKey(0)

text = "Found {} coins".format(len(contours))
cv2.putText(output, text, (25, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (240, 0, 159), 5)
# cv2.imshow("Contours", output)
# cv2.waitKey(0)

erosionImage = thresholdImage.copy()
erosionImage = cv2.erode(erosionImage, None, iterations=3)
# cv2.imshow("Erosion Image", erosionImage)
# cv2.waitKey(0)

dilationImage = thresholdImage.copy()
dilationImage = cv2.dilate(dilationImage, None, iterations=5)
# cv2.imshow("Dilation Image", dilationImage)
# cv2.waitKey(0)

andBitwiseImage = cv2.bitwise_and(image, image, mask=thresholdImage.copy())
cv2.imshow("Mask - AND", andBitwiseImage)
cv2.waitKey(0)