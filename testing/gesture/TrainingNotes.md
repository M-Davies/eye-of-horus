# Notes

This document contains info on my progress and vision for the machine learning model that will be able to tell a human gesture on stream.

## Gathering of training images

*See [#16](https://github.com/M-Davies/eye-of-horus/issues/16) for the work item of this*

AWS requires training images to be obtained and ran through the machine learning algorithm in order for it to identify a gesture a user is making on stream. To ensure as accurate machine learning algorithm as possible, we will be creating or retrieving a set of images containing the [proposed gestures](#AvailableGestures) to use for the training data set. The images need to be diverse, in large quantity, in a similar location to where the program will actually be used and clearly containing the training data we need for the algorithm to pick out the gestures from a sea of different objects. AWS defines a [series of standards](https://docs.aws.amazon.com/rekognition/latest/customlabels-dg/gs-step-prepare-images-cli.html) that we will try our best to stick to when creating the images.

NOTE: The following standards are all minimum requirements. It is likely that we will have more pictures than the target 50 (a good thing).

### Quantity

I intend to utilise 50 images for each [proposed gesture](#AvailableGestures).

Of these, **40 will be images I have taken and created myself, 10 being images I have pulled from the internet** to further train the model on unexpected or poor quality scenarios.

Of the 40 images, **20 will be created on my laptop camera and 20 on my phone camera** (to capture different resolutions).

### Quality

Of the 40 images I will create myself for each gesture, to ensure a diverse model, I will produce them in a set of different locations, angles and contexts:

- 10 images in low light
- 10 images in bright light
- 10 images in a neat background
- 10 images in a cluttered background

### Final Schema

*EXAMPLE FOR ONE GESTURE (so times this by 4 to get the total image count of 200):*

- **SELF IMAGES (40)**
  - *PHONE IMAGES (20)*
    - LOW LIGHT (5)
      - Neat Background (3)
      - Cluttered Background (2)
    - BRIGHT LIGHT (5)
      - Cluttered Background (3)
      - Neat Background (2)
  - *LAPTOP IMAGES (20)*
    - LOW LIGHT (5)
      - Neat Background (3)
      - Cluttered Background (2)
    - BRIGHT LIGHT (5)
      - Cluttered Background (3)
      - Neat Background (2)
- **INTERNET IMAGES (10)**
  - These are ambiguous and used to induce random data. As such, we will not split them up into sections based on the environment.

## Available Gestures

These gestures will be the initial "default" gestures user's can incorporate into their gesture unlock and lock patterns. More intend to be added over time but right now, this will be more than acceptable for my university demonstration and assignment.

- open-hand (hand is open with fingers together)

![image of open hand](https://previews.123rf.com/images/photobyphotoboy/photobyphotoboy1505/photobyphotoboy150500095/39489629-open-hand.jpg)

- closed-hand (hand is closed with fingers together)

![image of closed hand](https://www.womansworld.com/wp-content/uploads/2016/07/thumb-on-top.jpg)

- three-fingers (hand is closed with the three central fingers pointing out)

![image of three fingers out](https://thumbs.dreamstime.com/b/hand-three-fingers-up-isolated-white-background-mail-95386768.jpg)

- thumb-out (hand is closed with thumb up or down, fingers together)

![image of thumbs up](data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxISEhUSEhEVExETFRgSFhIYEhAPFxIVFxUXFxUVFRUYHSggGBolHRUVITEhJSkrLi4uFx8zODMsNygtLisBCgoKDg0OGBAQGy0mICYtLS0rLy0tLS0tLSstKy4tLS0tMS8rLS0tLy0tLS0tLS0tLS0tLS0vLSstLSstLS0tLf/AABEIAMsA+QMBIgACEQEDEQH/xAAbAAEAAgMBAQAAAAAAAAAAAAAABAUCAwYHAf/EADgQAAIBAgMFBgQFBAIDAAAAAAABAgMRBCExBQYSQVEiYXGBkaETMlKxQnLB0fAjQ4LhFGIHssL/xAAaAQEAAwEBAQAAAAAAAAAAAAAAAgMFBAEG/8QAJREBAQACAQQBBAMBAAAAAAAAAAECEQMEEiExIhNBUZEyUmEz/9oADAMBAAIRAxEAPwD3EAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEbadRxo1JJ2cac2n0ai2mcPsLaFRSb43e/Nt3z0a5lPLzTjsljo4envLLZfT0EGvDVlOKktGvTqjYWy78qLNXVAAevAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQttVowoVZS+XgkvFtWS820jz3ZDu/5yLjfXaXxJrDxfZg7z75vReSfq+4ibHw1pWM3quTuz7Y1+i4+zC5X7us2BN8Mo8lZrzvf7e5bFVsbWdtEl+panbwfwjP6j/pQAFqgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAI20cZGjTlUlpFadXol5uxJbOI3k2p/yJqnTf9KD1+uWl/BZpeL7irm5JhjtdwcV5MtKXCwdSo5PNtuTfe3d+7OkwdLhT8CNs/CqKLOnBu0VzdjLxm7tq55amlnsWjwwu9ZO/l/LvzLAxhFJJLRKxka+GPbjIx+TLuyuQACSAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHxsDjd6NuuTlRpu0E+GT5za1X5fv4a02BpZ3ZB4m3d66lzgoXMbkzud3W7w4Y8eOouaSyRZ7Lp3m39K93l+5WQdkTtkV7Ta+te6/1cv4dd825ueW4ZaXQBX4vbeGpZTrQTWsU+Nr/GN2aNsntmSW+lgDn574YVOyc2tLqDSv52fsZx3uwnOcl406n6Ih9XD8xZ9Hk/rf0vQUM98MGv7rb6fDq/qiVht4MPOXBGp2ujjOPu1Y9+rh+Z+3n0eT+t/S0ABNWAAAAAAAAAAAAAAAAAAAAAAAAEbaVXgpVJfTCT9IsklPvZW4cLPrLhj6yV/a5HO6xtSwm8pHni5F7gc0ihi8zoNnGM3LfC1pxVjTUi75Np9U7e5KhDI11S2zwpxy8uZ266mkqs5rkpTm013JvU5eGKSqOm3quKP6r7FjvLtXilaP4WctiZ8dSNtWnZrW60/neR81fJIu8RiGoP6oNS8bfujZSxPEuzm9bkPDYWpKK48npbX1L7Ymx4xSSWS65/cjfCzT5s7AN5u7fXqX+DwKTTt/sm4fDKJu4VrpbnoR1b7VXP8LzZNW8eG9+HTw6eRPKrYVaEk+Gak9LLp170Wpr8F3hGNzzXJQAFqoAAAAAAAAAAAAAAAAAAAAADl9/K9qdOH1Sc/KKt/wDR1B5pvVtNVq8uF3hDsRfW2r8235WOfqc+3DX5dPS4d3JL+Ffh43kdJs+NihwSOgwOhmT21MvS3gsjVVibqWgqLI6bPDll1XiW16nDOa6SkvRtHU7C2QowTsuJq7k88+7uKH/yPh1RrLhvepeVlnnKT0N+A3nrwpRUsPH4iVm/i282lF+lymx3YXbo8XgXBcfFdXs+Vr6WJ2zZrhzOLq43F1/nqqnD6IRVvNyu2XeyNmKWc5Of5m5L00IZ6Tm9eXQVdspvhor4kvq0gvP8Xl6mp4KdR3qzcufB8sF/j+92S6OHS0ROjDI8m6qtmPp92bHhtw5W08TqacrpPqkznMFTfEorN62/nI6OnGyS6KxodJLJWZ1llsZAA7HGAAAAAAAAAAAAAAAAAAAasTiYU4udScYQWspNRS82cjvDvxGm3TwyVSaydR5wi/8Arb537eJx1adbEy46s5VHyb0X5Y6RXgjm5epxwdXD0mefm+I6jeHe74qdLDX4HlKq04ua5qCeaX/Z+XU5LNPPmXWDwNkacfQUXno80+jM7PmvJlutPj4ceOahhy52dWvkUuGfItcDqeROzw6OhLI+1XkR6Ehi6ySbbslm34F9y+Lk7fk843r4Z7SUZfgoKSXfKWvo/cyhhY9F6Iod6Y1sVX+PRtTeik27uKyXZs+XU00MDi2rTxTX5Y297kJr3t2Y7k1pbxaU3Ho7HV7FkkjkNl7rO93Xqy5/Ml9kdThtiRSs3KS6SlKS9GyrLX2S348rWW0aUXbi4pdI9rPvtkvMk4DFSm12LRvo3m14rT3NVDCRiskkb8KrPoJtVlrVdZhYRUU4xsnn3+fVm40YH5F5/dm82sP4xh5/yoACSIAAAAAAAAAAAAAAAAzzbfHe11m8Ph5f0tJ1F/d6xi/o7+fhr9333s+LJ4XDy/p6VKi/G+cIv6er56aa0ey8CtWcPU9Rr44tDpel38sn3AYDRvQuaNBLRZCEORvoozLdtT0208jDaeGU4NdeZs7iYqXZtz1R7EMq5KhCUHwy8n1RfbPRnicLFrTLXw70fMLTce/2ZOU9xbU3lz9Cq3mqP/j1HZ/hT/K5JSb/AMblpRldCcb3TV08rFtm4pl1ltw1GHoRcd2Zq3mXm9eCdLDynQXDPijFatJSko3t3XOMeExV7uqvKEf2PPc06JlvzHYbKqLIvKaVjz/CTqp2dV+kV9kd5sRKUVfN9XmV686eZ+tptKS0WfgTNm4WMpri0z7Pf3v1CjFLVInbJoP57Wjy7+/wOnhw3lI4eXk1jbFmkfQDUZYAAAAAAAAAAAAAAAAed7+b35vC4aXWNWqnp1pwfXq/LrbPfnfK3FhcLLtfLUqp/L1hB/V1fLRZ6cZs/AnH1HUa+OLu6bpu75ZM9l4TnY6OjBJEXC0bZE+ETLyu2tJoRugYJE/DULK7PC3T7Sp2WZthOzuaKlW+htpK5KK7/rY4WduT0MaNPVc0zZisqTb1g1K/g8/YjYered+Uif3ivHdlTacbOxlJmMZ5synJFk9IXe2NXDqcXGSTjLJrqimr7rxeXxZJeCZdRq2LDDYCU853jHp+J/t9yzHDvvhHLkvHPNcfhty7zSjUbWfFLhXZ0tzz5+h1WB3YhT/uTa6dlfoXdKkoq0VZGZ2YdNhJ58uLk6vky9XUR6WBpx0gr9X2n6skAF8knpzW2+wAHrwAAAAAAAAAAAAAAAB4FgMNzZf4anYj4bDlnSpmFldvo8ZpnTWZJRqpkjD07srr1IwtHmzfiKtsjPJIgVJXfme+kPdbKEbvxLKhSsjTgqRIrzSJ4z71Vnlu6iNtR3o1VfWEvsVuysTeEJvLs+7OiWwPjQfxJygpL5Y2Ttzu2na/QttnbLpUIqNOOn4nnJ+Z04dLnn5vhRer48JZPNc7Swddq8aUnfq4w/8AZok4fY1eXzuMF48b9Fl7nSg6sekwnvdc2XW8l9aiHg9nQp5pXl9Tzfl0JgB044zGajlyyuV3QAHqIAAAAAAAAAAAAAAAAAAAAA8ooqyJVIj0okmJgV9IyisyfRVkRaMSSmRRyr7WnlYxw9K5sUbkvD0SWM3UMstRuiuFEvY+D438SXyp9ldWufl9/AixpupOMFz1fRc2dLTpqKUUrJKyR3dNxd17r6jP6jl7Zqe6yABouAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAeXwib6cAlkbqKMCvo9tsVZGyB8iboo80ha2UYXJFSdkY0Vka6qu4p6OcU11Tkky3GfaOfK+V5sPDWh8R/NPNd0eXrr6FmAbOGEwxmMZOeVyytoACSIAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//2Q==)

![image of thumbs down](https://www.sentara.com/Assets/Img/Health-Wellness/ExploreHealth-With-Sentara/Rectangle/thumbs-down.jpg?width=715&height=455)

## Optimal Results for eye-of-horus-gesture-project.2021-03-17T13.54.11

These are the recommended specifications to create your gesture images against. This will minimise false positives and negatives:

- Ensure that in your image, the gesture is taking up the majority of the foreground and that the background is not cluttered or containing any hands of any kind (even non-human ones!)
- For `closed-hand` images, the palm needs to be facing AWAY from camera
- For `open-hand` images, the palm needs to be facing TOWARDS camera
- For `thumb-out` images, the palm needs to be facing AWAY from camera (thumb down)
- For `three-fingers` images, the three fingers need to facing HORIZONTAL with the palm TOWARDS the camera
