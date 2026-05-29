import cv2 as cv

def resize_image(input_path, output_path, width=None, height=None):
    image = cv.imread(input_path)
    if image is None:
        print(f"Error: Could not read image from {input_path}")
        return
    
    if width is None and height is None:
        print("Error: At least one of width or height must be provided.")
        return
    elif width is None:
        aspect_ratio = image.shape[1] / image.shape[0]
        width = int(height * aspect_ratio)

    elif height is None:
        aspect_ratio = image.shape[0] / image.shape[1]
        height = int(width * aspect_ratio)
    resized_image = cv.resize(image, (width, height))   
    cv.imwrite(output_path, resized_image)
    print(f"Image resized and saved to {output_path}")

resize_image('IMG_4685.JPG', 'resized_imaged.jpg', width=50)    
