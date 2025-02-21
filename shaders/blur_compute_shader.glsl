#version 430
layout (local_size_x = 16, local_size_y = 16) in;

layout (rgba32f, binding = 0) uniform image2D inputTexture;
layout (rgba32f, binding = 1) uniform image2D outputTexture;
layout (r8, binding = 3) uniform image2D backgroundTexture;

int blurSize = 1;
float decayRate = 0.995; // 0.98

void main() {
    ivec2 texSize = imageSize(inputTexture);
    ivec2 pixelCoord = ivec2(gl_GlobalInvocationID.xy);

    if (pixelCoord.x >= texSize.x || pixelCoord.y >= texSize.y) {
        return;
    }

    float is_valid_position = imageLoad(backgroundTexture, ivec2(pixelCoord)).r;
    if(is_valid_position == 0) {
        return;
    }

    vec3 color = vec3(0.0);
    int count = 0;

    for (int x = -blurSize; x <= blurSize; x++) {
        for (int y = -blurSize; y <= blurSize; y++) {
            ivec2 coord = pixelCoord + ivec2(x, y);
            if (coord.x >= 0 && coord.x < texSize.x && coord.y >= 0 && coord.y < texSize.y) {
                color += imageLoad(inputTexture, coord).xyz;
                count++;
            }
        }
    }

    color /= float(count);
    color.xyz *= vec3(decayRate);
    imageStore(outputTexture, pixelCoord, vec4(color, 1.0));
}