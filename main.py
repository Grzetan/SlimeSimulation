# import glfw
# from OpenGL.GL import *
# from OpenGL.GL.shaders import compileProgram, compileShader


# # Vertex shader: Passes through vertex positions
# VERTEX_SHADER = """
# #version 430 core
# void main() {
#     const vec2 positions[4] = vec2[4](
#         vec2(-1.0, -1.0),
#         vec2( 1.0, -1.0),
#         vec2(-1.0,  1.0),
#         vec2( 1.0,  1.0)
#     );
#     gl_Position = vec4(positions[gl_VertexID], 0.0, 1.0);
# }
# """

# # Fragment shader: Alternates pixels between two colors based on index
# FRAGMENT_SHADER = """
# #version 430 core
# out vec4 fragColor;

# uniform vec4 color1;
# uniform vec4 color2;

# void main() {
#     // Calculate the pixel index based on screen coordinates
#     ivec2 pixelCoord = ivec2(gl_FragCoord.xy);
#     int pixelIndex = pixelCoord.x + pixelCoord.y;

#     // Apply a simple blur effect by averaging the colors of neighboring pixels
#     /*vec4 sum = vec4(0.0);
#     for (int dx = -1; dx <= 1; ++dx) {
#         for (int dy = -1; dy <= 1; ++dy) {
#             ivec2 neighborCoord = pixelCoord + ivec2(dx, dy);
#             sum += texelFetch(sampler2D(gl_FragCoord.xy), neighborCoord, 0);
#         }
#     }*/

#     fragColor = vec4(1.0,0.0,1.0,0.0);

# }
# """


# def create_shader_program(vertex_src, fragment_src):
#     return compileProgram(
#         compileShader(vertex_src, GL_VERTEX_SHADER),
#         compileShader(fragment_src, GL_FRAGMENT_SHADER),
#     )


# def main():
#     # Initialize GLFW
#     if not glfw.init():
#         return

#     # Create GLFW window
#     window = glfw.create_window(800, 600, "Shader Example", None, None)
#     if not window:
#         glfw.terminate()
#         return

#     glfw.make_context_current(window)

#     # Compile and use shader program
#     shader_program = create_shader_program(VERTEX_SHADER, FRAGMENT_SHADER)
#     glUseProgram(shader_program)

#     # Set uniform colors
#     color1_location = glGetUniformLocation(shader_program, "color1")
#     color2_location = glGetUniformLocation(shader_program, "color2")
#     glUniform4f(color1_location, 1.0, 0.0, 1.0, 1.0)  # White color
#     glUniform4f(color2_location, 0.0, 1.0, 0.0, 1.0)  # Black color

#     # Main loop
#     while not glfw.window_should_close(window):
#         glClear(GL_COLOR_BUFFER_BIT)

#         # Draw fullscreen quad
#         glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

#         glfw.swap_buffers(window)
#         glfw.poll_events()

#     # Cleanup
#     glDeleteProgram(shader_program)
#     glfw.terminate()


# if __name__ == "__main__":
#     main()

from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glfw
import numpy as np

COMPUTE_SHADER = """
#version 430
layout (local_size_x = 8, local_size_y = 1, local_size_z = 1) in;
layout (std430, binding = 0) buffer SSBO {
    vec2 pos[];
} ssbo;

uniform float time;

void main() {
    uint threadIndex = gl_GlobalInvocationID.x;
    float floatIndex = float(threadIndex);
    ssbo.pos[threadIndex] = vec2(floatIndex * 0.25 - 0.875, 0.5 * sin(time * 0.02 + floatIndex * 0.5));
}
"""

VERTEX_SHADER = """
#version 430
layout (location = 0) in vec2 position;

void main() {
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 430
precision highp float;
    
out vec4 outColor;

void main() {
    outColor = vec4(1.0, 1.0, 1.0, 1.0);
}
"""


def create_compute_shader_program(compute_src):
    return compileProgram(
        compileShader(compute_src, GL_COMPUTE_SHADER),
    )


def create_shader_program(vertex_src, fragment_src):
    return compileProgram(
        compileShader(vertex_src, GL_VERTEX_SHADER),
        compileShader(fragment_src, GL_FRAGMENT_SHADER),
    )


def main():
    # Initialize GLFW
    if not glfw.init():
        return

    # Create GLFW window
    window = glfw.create_window(800, 600, "Compute Shader Example", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    # Compile and use compute shader program
    compute_program = create_compute_shader_program(COMPUTE_SHADER)
    time_location = glGetUniformLocation(compute_program, "time")

    # Create Shader Storage Buffer Object (SSBO)
    ssbo = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, ssbo)
    data = np.zeros(16, dtype=np.float32)
    glBufferData(GL_SHADER_STORAGE_BUFFER, data.nbytes, data, GL_DYNAMIC_COPY)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, ssbo)

    shader_program = create_shader_program(VERTEX_SHADER, FRAGMENT_SHADER)

    glBindBuffer(GL_ARRAY_BUFFER, ssbo)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

    time = 0.0
    # Main loop
    while not glfw.window_should_close(window):
        time += 1.0

        glUseProgram(compute_program)

        # Update time uniform
        glUniform1f(time_location, time)

        # Dispatch compute shader
        glDispatchCompute(1, 1, 1)
        glMemoryBarrier(GL_VERTEX_ATTRIB_ARRAY_BARRIER_BIT)

        glClear(GL_COLOR_BUFFER_BIT)

        glUseProgram(shader_program)

        glDrawArrays(GL_POINTS, 0, 8)

        glfw.swap_buffers(window)
        glfw.poll_events()

    # Cleanup
    glDeleteProgram(compute_program)
    glDeleteProgram(shader_program)
    glDeleteBuffers(1, [ssbo])
    glfw.terminate()


if __name__ == "__main__":
    main()
