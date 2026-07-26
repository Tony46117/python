from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "engine",
        ["engine.cpp"],
        extra_compile_args=["-std=c++17", "-O3"],
    )
]

setup(
    name="snake_engine",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
