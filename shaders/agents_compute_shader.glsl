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

    ssbo.data[index] += vec2(1.0, 0.0);

    float floatIndex = float(index);

    vec2 value = ssbo.data[index];
    for(int i=-10; i<=10; i++) {
        for(int j=-10; j<=10; j++) {
            imageStore(outputTexture, ivec2(value) + ivec2(i, j), vec4(1.0, 1.0, 1.0, 1.0));
        }
    }
}