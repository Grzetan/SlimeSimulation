from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glfw
import numpy as np

local_size_x = 16
local_size_y = 16

# Compute Shader: Uses SSBO for data and writes to a texture
COMPUTE_SHADER = """
#version 430
layout (local_size_x = 8, local_size_y = 1) in;

layout (std430, binding = 0) buffer SSBO {
    vec2 data[];
} ssbo;

uniform uint ssboSize;

layout (rgba32f, binding = 0) uniform image2D outputTexture;

void main() {
    uint index = gl_GlobalInvocationID.x;

    if (index >= ssboSize) {
        return;
    }

    float floatIndex = float(index);

    vec2 value = ssbo.data[index];
    for(int i=-10; i<=10; i++) {
        for(int j=-10; j<=10; j++) {
            imageStore(outputTexture, ivec2(value) + ivec2(i, j), vec4(1.0, 1.0, 1.0, 1.0));
        }
    }
}
"""

SECOND_COMPUTE_SHADER = f"""
#version 430
layout (local_size_x = {local_size_x}, local_size_y = {local_size_y}) in;

layout (rgba32f, binding = 0) uniform image2D inputTexture;
layout (rgba32f, binding = 1) uniform image2D outputTexture;

void main() {{
    ivec2 texSize = imageSize(inputTexture);
    ivec2 pixelCoord = ivec2(gl_GlobalInvocationID.xy);

    if (pixelCoord.x >= texSize.x || pixelCoord.y >= texSize.y) {{
        return;
    }}

    vec4 color = vec4(0.0);
    int blurSize = 9;
    int count = 0;

    for (int x = -blurSize; x <= blurSize; x++) {{
        for (int y = -blurSize; y <= blurSize; y++) {{
            ivec2 coord = pixelCoord + ivec2(x, y);
            if (coord.x >= 0 && coord.x < texSize.x && coord.y >= 0 && coord.y < texSize.y) {{
                color += imageLoad(inputTexture, coord);
                count++;
            }}
        }}
    }}

    color /= float(count);
    imageStore(outputTexture, pixelCoord, color);
}}

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
    //vec2 tex_offset = 1.0 / textureSize(inputTexture, 0); // gets size of single texel
    outColor = texture(inputTexture, fragTexCoord);
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
    width = 800
    height = 600
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
    ssbo = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, ssbo)
    glBufferData(GL_SHADER_STORAGE_BUFFER, ssbo_data.nbytes, ssbo_data, GL_DYNAMIC_COPY)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, ssbo)

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

    ssbo_size_location = glGetUniformLocation(compute_program, "ssboSize")
    glUseProgram(compute_program)
    glUniform1ui(ssbo_size_location, ssbo_data.shape[0])

    num_groups_x_2 = (width + local_size_x - 1) // local_size_x
    num_groups_y_2 = (height + local_size_y - 1) // local_size_y

    while not glfw.window_should_close(window):
        # Use compute shader to draw and update agents
        glUseProgram(compute_program)
        glBindImageTexture(0, textures[0], 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA32F)
        num_groups_x = (max(ssbo_data.shape[0], 1) + 8 - 1) // 8
        glDispatchCompute(num_groups_x, 1, 1)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

        # Optional: Execute the second compute shader
        glUseProgram(second_compute_program)
        glBindImageTexture(0, textures[0], 0, GL_FALSE, 0, GL_READ_ONLY, GL_RGBA32F)
        glBindImageTexture(1, textures[1], 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA32F)
        glDispatchCompute(num_groups_x_2, num_groups_y_2, 1)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

        # Render the texture to the screen
        glUseProgram(render_program)
        glBindTexture(GL_TEXTURE_2D, textures[1])
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

        textures = textures[::-1]
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
