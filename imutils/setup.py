from distutils.core import setup

setup(
    name='imutils',
    packages=['imutils', 'imutils.video', 'imutils.io', 'imutils.feature', 'imutils.face_utils'],
    version='0.5.4',
    description='A series of convenience functions to make basic image processing functions such as translation, rotation, resizing, skeletonization, displaying Matplotlib images, sorting contours, detecting edges, and much more easier with OpenCV and both Python 2.7 and Python 3.',
    author='Adrian Rosebrock/Pawel Kapusta (fork)',
    author_email='adrian@pyimagesearch.com; pawel.kapusta@p.lodz.pl',
    url='https://github.com/jrosebr1/imutils; https://github.com/pawelplodzpl/imutils ',
    keywords=['computer vision', 'image processing', 'opencv', 'matplotlib'],
    classifiers=[],
    scripts=['bin/range-detector'],
)
