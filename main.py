import os
from cvzone.HandTrackingModule import HandDetector
import cv2
import pyttsx3
import pygame
import uuid

# Initialize pygame mixer
pygame.mixer.init()

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# Load images with error checks
imgBackground = cv2.imread("Resources/Resources/Background.png")
if imgBackground is None:
    raise ValueError("Error: Background image not found or failed to load.")

order_confirmation_image = cv2.imread("Resources/Resources/OrderConfirmation.png")
if order_confirmation_image is None:
    raise ValueError("Error: Order confirmation image not found or failed to load.")

# Load feedback prompt image with error handling
feedback_prompt_image_path = "Resources/Resources/FeedbackPrompt.png"
feedback_prompt_image = cv2.imread(feedback_prompt_image_path)
if feedback_prompt_image is None:
    print(f"Warning: Feedback prompt image '{feedback_prompt_image_path}' not found or failed to load.")
    feedback_prompt_image = imgBackground  # Use a default image or blank background

# Importing all the mode images to a list
folderPathModes = "Resources/Resources/Modes"
listImgModesPath = os.listdir(folderPathModes)
listImgModes = []
for imgModePath in listImgModesPath:
    img = cv2.imread(os.path.join(folderPathModes, imgModePath))
    if img is None:
        print(f"Error: Mode image '{imgModePath}' not found or failed to load.")
    else:
        listImgModes.append(img)

# Importing all the icons to a list
folderPathIcons = "Resources/Resources/Icons"
listImgIconsPath = os.listdir(folderPathIcons)
listImgIcons = []
for imgIconsPath in listImgIconsPath:
    img = cv2.imread(os.path.join(folderPathIcons, imgIconsPath))
    if img is None:
        print(f"Error: Icon image '{imgIconsPath}' not found or failed to load.")
    else:
        listImgIcons.append(img)

# Ensure all images have the same dimensions
bg_height, bg_width, _ = imgBackground.shape
for img in listImgModes:
    if img.shape[0] != bg_height or img.shape[1] != bg_width:
        img = cv2.resize(img, (bg_width, bg_height))

order_confirmation_image = cv2.resize(order_confirmation_image, (bg_width, bg_height))
feedback_prompt_image = cv2.resize(feedback_prompt_image, (bg_width, bg_height))

modeType = 0
selection = -1
counter = 0
selectionSpeed = 7
detector = HandDetector(detectionCon=0.8, maxHands=1)
modePositions = [(1136, 196), (1000, 384), (1136, 581)]
counterPause = 0
selectionList = [-1, -1, -1]
feedbackMode = False

# Define item names for each selection
item_names = {
    1: "Coffee",
    2: "Latte",
    3: "Cappuccino"
}


def play_sound(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()


def save_feedback(feedback):
    with open("feedback.txt", "a") as f:
        f.write(f"{uuid.uuid4()}: {feedback}\n")


resetCounter = 0
resetHoldTime = 30
confirmation_display_time = 200
confirmation_sent = False

while True:
    success, img = cap.read()
    if not success:
        break

    hands, img = detector.findHands(img)
    imgBackground[139:139 + 480, 50:50 + 640] = img
    imgBackground[0:720, 847: 1280] = listImgModes[modeType]

    if hands and counterPause == 0 and modeType < 3:
        hand1 = hands[0]
        fingers1 = detector.fingersUp(hand1)
        print(fingers1)

        if fingers1 == [0, 0, 0, 0, 0]:
            resetCounter += 1
            if resetCounter > resetHoldTime:
                print("Reset gesture detected")
                modeType = 0
                selectionList = [-1, -1, -1]
                engine.say("Mode selection reset")
                engine.runAndWait()
                resetCounter = 0
        else:
            resetCounter = 0

        if fingers1 == [0, 1, 0, 0, 0]:
            if selection != 1:
                counter = 1
            selection = 1
        elif fingers1 == [0, 1, 1, 0, 0]:
            if selection != 2:
                counter = 1
            selection = 2
        elif fingers1 == [0, 1, 1, 1, 0]:
            if selection != 3:
                counter = 1
            selection = 3
        else:
            selection = -1
            counter = 0

        if counter > 0:
            counter += 1
            print(counter)

            cv2.ellipse(imgBackground, modePositions[selection - 1], (103, 103), 0, 0,
                        counter * selectionSpeed, (0, 255, 0), 20)

            radius = int(counter * 3)
            cv2.circle(imgBackground, modePositions[selection - 1], radius, (0, 255, 255), 5)

            if counter * selectionSpeed > 360:
                selectionList[modeType] = selection

                engine.say(f"Selection {selection} confirmed")
                engine.runAndWait()

                play_sound('Resources/Resources/Sounds/selection_sound.mp3')

                modeType += 1
                counter = 0
                selection = -1
                counterPause = 1

    if counterPause > 0:
        counterPause += 1
        if counterPause > 60:
            counterPause = 0

    if all(sel != -1 for sel in selectionList) and modeType >= 3:
        if not confirmation_sent:
            # Display an image prompting the user to wait for confirmation
            imgBackground[:] = 0  # Clear the background
            cv2.putText(imgBackground, "Processing your order, please wait...",
                        (50, 360), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.imshow("Background", imgBackground)
            cv2.waitKey(3000)  # Wait for 3 seconds before showing confirmation

            imgBackground[0:720, 0:1280] = order_confirmation_image
            cv2.putText(imgBackground, "Order confirmed!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Display detailed order confirmation message
            order_reference = str(uuid.uuid4())
            selected_items = [item_names.get(item_id, "Unknown Item") for item_id in selectionList]
            confirmation_message = (
                f"Items: {', '.join(selected_items)}\n"
                f"Order Reference: {order_reference}\n"
                f"Thank you for your purchase!"
            )
            y0, dy = 200, 40
            for i, line in enumerate(confirmation_message.split('\n')):
                y = y0 + i * dy
                cv2.putText(imgBackground, line, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            cv2.imshow("Background", imgBackground)
            cv2.waitKey(1)

            confirmation_sent = True
            counterPause = confirmation_display_time
            feedbackMode = True  # Switch to feedback mode

    if feedbackMode:
        imgBackground[:] = 0  # Clear the background
        imgBackground[0:720, 0:1280] = feedback_prompt_image
        cv2.putText(imgBackground, "Please provide your feedback.", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (255, 255, 255), 2)

        if hands:
            hand1 = hands[0]
            fingers1 = detector.fingersUp(hand1)
            print(fingers1)

            if fingers1 == [0, 0, 0, 0, 1]:  # Example gesture to finish feedback
                feedback_start_time = cv2.getTickCount()
                feedback = ""

                while True:
                    hands, img = detector.findHands(img)
                    imgBackground[139:139 + 480, 50:50 + 640] = img
                    imgBackground[0:720, 847: 1280] = listImgModes[modeType]

                    cv2.putText(imgBackground, "Recording feedback...", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (255, 255, 255), 2)
                    cv2.imshow("Background", imgBackground)

                    if cv2.getTickCount() - feedback_start_time > 50000000:  # Example time limit (1 second)
                        break

                    cv2.waitKey(1)
                save_feedback(feedback)
                engine.say("Thank you for your feedback!")
                engine.runAndWait()
                feedbackMode = False
                confirmation_sent = False

    if selectionList[0] != -1:
        imgBackground[636:636 + 65, 133:133 + 65] = listImgIcons[selectionList[0] - 1]
    if selectionList[1] != -1:
        imgBackground[636:636 + 65, 340:340 + 65] = listImgIcons[2 + selectionList[1]]
    if selectionList[2] != -1:
        imgBackground[636:636 + 65, 542:542 + 65] = listImgIcons[5 + selectionList[2]]

    if not confirmation_sent and not feedbackMode:
        cv2.imshow("Background", imgBackground)
    cv2.waitKey(1)

cap.release()
cv2.destroyAllWindows()
