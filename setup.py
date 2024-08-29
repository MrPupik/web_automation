from distutils.core import setup

setup(
    name="decent-selenium",
    version="0.12",
    packages=[
        "web_automation",
    ],
    license="MIT",
    package_dir={
        "web_automation": ".",
    },
    long_description="Web Automation Tools",
)
