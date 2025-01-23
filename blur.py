from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glfw
import numpy as np

local_size_x = 16
local_size_y = 16
width = 1920
height = 1080
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
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, None
        )
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

    time_location = glGetUniformLocation(agent_compute_program, "time")
    glUseProgram(agent_compute_program)
    glUniform1ui(time_location, input_data["time"])
    return {"ssboSize": ssbo_size_location, "time": time_location}


def create_agents():
    agent_size = 500000
    agents = np.zeros((agent_size, 4), dtype=np.float32)
    radius = 300
    center_x, center_y = width / 2, height / 2

    for i in range(agent_size):
        angle = np.random.uniform(0, 2 * np.pi)
        r = radius * np.sqrt(np.random.uniform(0, 1))
        agents[i, 0] = center_x + r * np.cos(angle)
        agents[i, 1] = center_y + r * np.sin(angle)
        dx = center_x - agents[i, 0]
        dy = center_y - agents[i, 1]
        agents[i, 2] = np.arctan2(dy, dx)
    return agents


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
    ssbo_data = create_agents()
    ssbo = bind_ssbo(ssbo_data)
    num_groups_x = (ssbo_data.shape[0] + 8 - 1) // 8

    textures = create_textures()

    agent_compute_program, blur_compute_program, render_program = create_programs()

    uniforms = fill_uniforms(
        agent_compute_program,
        blur_compute_program,
        render_program,
        {"ssboSize": ssbo_data.shape[0], "time": 0},
    )

    time = 0
    while not glfw.window_should_close(window):
        # Blur the texture
        glUseProgram(blur_compute_program)
        glBindImageTexture(0, textures[0], 0, GL_FALSE, 0, GL_READ_ONLY, GL_RGBA32F)
        glBindImageTexture(1, textures[1], 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA32F)
        glDispatchCompute(num_groups_x_blur, num_groups_y_blur, 1)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

        # Use compute shader to draw and update agents
        glUseProgram(agent_compute_program)
        glUniform1ui(uniforms["time"], time)
        glBindImageTexture(1, textures[0], 0, GL_FALSE, 0, GL_READ_ONLY, GL_RGBA32F)
        glBindImageTexture(2, textures[1], 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA32F)
        glDispatchCompute(num_groups_x, 1, 1)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

        # Render the texture to the screen
        glUseProgram(render_program)
        glBindTexture(GL_TEXTURE_2D, textures[1])
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

        textures = textures[::-1]
        glfw.swap_buffers(window)
        glfw.poll_events()
        time += 1

    # Cleanup
    glDeleteProgram(agent_compute_program)
    glDeleteProgram(blur_compute_program)
    glDeleteProgram(render_program)
    glDeleteBuffers(1, [ssbo])
    glDeleteTextures(textures)
    glfw.terminate()


if __name__ == "__main__":
    main()
