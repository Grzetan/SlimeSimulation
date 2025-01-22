from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glfw
import numpy as np

local_size_x = 16
local_size_y = 16
width = 800
height = 600
num_groups_x_blur = (width + local_size_x - 1) // local_size_x
num_groups_y_blur = (height + local_size_y - 1) // local_size_y


def create_compute_shader_program(compute_src):
    return compileProgram(
        compileShader(compute_src, GL_COMPUTE_SHADER),
    )


def create_shader_program(vertex_src, fragment_src):
    return compileProgram(
        compileShader(vertex_src, GL_VERTEX_SHADER),
        compileShader(fragment_src, GL_FRAGMENT_SHADER),
    )


def bind_ssbo(ssbo_data):
    ssbo = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, ssbo)
    glBufferData(GL_SHADER_STORAGE_BUFFER, ssbo_data.nbytes, ssbo_data, GL_DYNAMIC_COPY)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, ssbo)
    return ssbo


def create_textures():
    textures = glGenTextures(2)
    for tex in textures:
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, 800, 600, 0, GL_RGBA, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    return textures


def create_programs():
    with open("shaders/agents_compute_shader.glsl") as f:
        agent_compute_program = create_compute_shader_program(f.read())

    with open("shaders/blur_compute_shader.glsl") as f:
        blur_compute_program = create_compute_shader_program(f.read())

    with open("shaders/vertex_shader.glsl") as vertex:
        with open("shaders/fragment_shader.glsl") as fragment:
            render_program = create_shader_program(vertex.read(), fragment.read())

    return agent_compute_program, blur_compute_program, render_program


def fill_uniforms(
    agent_compute_program, blur_compute_program, render_program, input_data
):
    ssbo_size_location = glGetUniformLocation(agent_compute_program, "ssboSize")
    glUseProgram(agent_compute_program)
    glUniform1ui(ssbo_size_location, input_data["ssboSize"])

    return {"ssboSize": ssbo_size_location}


def main():
    # Initialize GLFW
    if not glfw.init():
        return

    # Create a GLFW window
    window = glfw.create_window(
        width, height, "Compute and Fragment Shader Example", None, None
    )
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    # Create SSBO
    ssbo_data = np.array(
        [[300, 100], [200, 200], [300, 300], [400, 400], [500, 500]]
    ).astype(np.float32)
    ssbo = bind_ssbo(ssbo_data)

    textures = create_textures()

    agent_compute_program, blur_compute_program, render_program = create_programs()

    uniforms = fill_uniforms(
        agent_compute_program,
        blur_compute_program,
        render_program,
        {"ssboSize": ssbo_data.shape[0]},
    )

    while not glfw.window_should_close(window):
        # Use compute shader to draw and update agents
        glUseProgram(agent_compute_program)
        glBindImageTexture(0, textures[0], 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA32F)
        num_groups_x = (max(ssbo_data.shape[0], 1) + 8 - 1) // 8
        glDispatchCompute(num_groups_x, 1, 1)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

        # Optional: Execute the second compute shader
        glUseProgram(blur_compute_program)
        glBindImageTexture(0, textures[0], 0, GL_FALSE, 0, GL_READ_ONLY, GL_RGBA32F)
        glBindImageTexture(1, textures[1], 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA32F)
        glDispatchCompute(num_groups_x_blur, num_groups_y_blur, 1)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

        # Render the texture to the screen
        glUseProgram(render_program)
        glBindTexture(GL_TEXTURE_2D, textures[1])
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

        textures = textures[::-1]
        glfw.swap_buffers(window)
        glfw.poll_events()

    # Cleanup
    glDeleteProgram(agent_compute_program)
    glDeleteProgram(blur_compute_program)
    glDeleteProgram(render_program)
    glDeleteBuffers(1, [ssbo])
    glDeleteTextures(textures)
    glfw.terminate()


if __name__ == "__main__":
    main()
