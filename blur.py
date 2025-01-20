from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glfw
import numpy as np

# Compute Shader: Uses SSBO for data and writes to a texture
COMPUTE_SHADER = """
#version 430
layout (local_size_x = 10, local_size_y = 1) in;

layout (std430, binding = 0) buffer SSBO {
    vec2 data[];
} ssbo;

layout (rgba32f, binding = 0) uniform image2D outputTexture;

void main() {
    uint index = gl_GlobalInvocationID.x;
    float floatIndex = float(index);

    vec2 value = ssbo.data[index];
    imageStore(outputTexture, ivec2(value), vec4(1.0, 1.0, 1.0, 1.0));
}
"""

# Vertex Shader: Pass-through
VERTEX_SHADER = """
#version 430
out vec2 fragTexCoord;

void main() {
    vec2 positions[4] = vec2[](
        vec2(-1.0, -1.0),
        vec2( 1.0, -1.0),
        vec2(-1.0,  1.0),
        vec2( 1.0,  1.0)
    );
    vec2 texCoords[4] = vec2[](
        vec2(0.0, 0.0),
        vec2(1.0, 0.0),
        vec2(0.0, 1.0),
        vec2(1.0, 1.0)
    );

    gl_Position = vec4(positions[gl_VertexID], 0.0, 1.0);
    fragTexCoord = texCoords[gl_VertexID];
}
"""

# Fragment Shader: Sample the texture and render it
FRAGMENT_SHADER = """
#version 430
in vec2 fragTexCoord;
out vec4 outColor;

uniform sampler2D inputTexture;

void main() {
    vec2 tex_offset = 1.0 / textureSize(inputTexture, 0); // gets size of single texel
    vec4 result = vec4(0.0);

    // Average the color of the surrounding 3x3 pixels
    for(int x = -1; x <= 1; x++) {
        for(int y = -1; y <= 1; y++) {
            vec2 offset = vec2(float(x), float(y)) * tex_offset;
            result += texture(inputTexture, fragTexCoord + offset);
        }
    }
    result /= 9.0; // divide by the number of samples
    outColor = result;
}
"""

SECOND_COMPUTE_SHADER = """
#version 430
layout (local_size_x = 1, local_size_y = 1) in;

layout (rgba32f, binding = 0) uniform image2D outputTexture;

void main() {
    ivec2 targetPixel = ivec2(0, 200);
    imageStore(outputTexture, targetPixel, vec4(1.0, 1.0, 1.0, 1.0));
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

    # Create a GLFW window
    window = glfw.create_window(
        800, 600, "Compute and Fragment Shader Example", None, None
    )
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    # Create SSBO
    ssbo_data = np.array([[10, 10], [20, 20], [30, 30], [40, 40], [799, 599]]).astype(
        np.float32
    )
    ssbo = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, ssbo)
    glBufferData(GL_SHADER_STORAGE_BUFFER, ssbo_data.nbytes, ssbo_data, GL_DYNAMIC_COPY)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, ssbo)

    # Create two textures for ping-pong buffering
    textures = glGenTextures(2)
    for tex in textures:
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, 800, 600, 0, GL_RGBA, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    # Compile shaders
    compute_program = create_compute_shader_program(COMPUTE_SHADER)
    second_compute_program = create_compute_shader_program(SECOND_COMPUTE_SHADER)
    render_program = create_shader_program(VERTEX_SHADER, FRAGMENT_SHADER)

    current_input = 0  # Index of the current input texture
    current_output = 1  # Index of the current output texture

    # Render loop
    while not glfw.window_should_close(window):
        # Execute the compute shader
        glUseProgram(compute_program)

        glBindImageTexture(
            0, textures[current_input], 0, GL_FALSE, 0, GL_READ_ONLY, GL_RGBA32F
        )
        glBindImageTexture(
            1, textures[current_output], 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA32F
        )

        glDispatchCompute(1, 1, 1)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

        glUseProgram(second_compute_program)
        glDispatchCompute(1, 1, 1)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

        # Render the texture
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(render_program)
        glBindTexture(GL_TEXTURE_2D, textures[current_output])
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

        current_input, current_output = current_output, current_input

        glfw.swap_buffers(window)
        glfw.poll_events()

    # Cleanup
    glDeleteProgram(compute_program)
    glDeleteProgram(render_program)
    glDeleteBuffers(1, [ssbo])
    glDeleteTextures(textures)
    glfw.terminate()


if __name__ == "__main__":
    main()
