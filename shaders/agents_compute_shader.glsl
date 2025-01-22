#version 430
layout (local_size_x = 8, local_size_y = 1) in;

struct Agent {
    vec2 position;
    float angle;
    float padding;
};

layout (std430, binding = 0) buffer SSBO {
    Agent agents[];
} ssbo;

uniform uint ssboSize;
uniform uint time;

layout (rgba32f, binding = 1) uniform image2D outputTexture;

uint random(uint state)
{
    state ^= 2747636419u;
    state *= 2654435769u;
    state ^= state >> 16;
    state *= 2654435769u;
    state ^= state >> 16;
    state *= 2654435769u;
    return state;
}

void main() {
    uint index = gl_GlobalInvocationID.x;
    if (index >= ssboSize) {
        return;
    }

    Agent agent = ssbo.agents[index];
    vec2 direction = vec2(cos(agent.angle), sin(agent.angle));
    agent.position += direction;

    ivec2 imageSize = imageSize(outputTexture);
    if (agent.position.x < 0.0 || agent.position.x >= imageSize.x || agent.position.y < 0.0 || agent.position.y >= imageSize.y) {
        agent.angle = float(random(time + index)) / 4294967295.0 * 2.0 * 3.1415;
        agent.position.x = min(imageSize.x-1,max(0, agent.position.x));
        agent.position.y = min(imageSize.y-1,max(0, agent.position.y));
    }

    ssbo.agents[index] = agent;

    // Draw agent
    int agentSize = 1;
    for (int x = -agentSize; x <= agentSize; x++) {
        for (int y = -agentSize; y <= agentSize; y++) {
            ivec2 coord = ivec2(agent.position) + ivec2(x, y);
            
            if (coord.x < 0 || coord.x >= imageSize.x || coord.y < 0 || coord.y >= imageSize.y) {
                continue;
            }

            imageStore(outputTexture, coord, vec4(1.0, 1.0, 1.0, 1.0));
        }
    }
}