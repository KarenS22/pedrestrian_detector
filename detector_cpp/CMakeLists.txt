cmake_minimum_required(VERSION 3.15)
project(PersonDetector)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Buscar OpenCV
find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

# Buscar libcurl para HTTP requests
find_package(CURL REQUIRED)
include_directories(${CURL_INCLUDE_DIR})

# Archivos fuente
set(SOURCES
    main.cpp
    utils/telegram_sender.cpp
)

# Crear ejecutable
add_executable(person_detector ${SOURCES})

# Linkear librerías
target_link_libraries(person_detector
    ${OpenCV_LIBS}
    ${CURL_LIBRARIES}
    pthread
)

# Opciones de compilación
target_compile_options(person_detector PRIVATE
    -Wall
    -Wextra
    -O3
)
