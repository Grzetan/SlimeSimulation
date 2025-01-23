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
float sensorAngleRad = 30 * (3.1415 / 180.0);
uint sensorSize = 5;
uint sensorOffset = 5;
float turnSpeed = 90 * (3.1415 / 180.0);

layout (rgba32f, binding = 1) uniform image2D outputTexture;

float random(uint state)
{
    state ^= 2747636419u;
    state *= 2654435769u;
    state ^= state >> 16;
    state *= 2654435769u;
    state ^= state >> 16;
    state *= 2654435769u;
    return state / 4294967295.0;
}

float sense(Agent agent, float sensorOffset, vec2 imageSize){
    vec2 direction = vec2(cos(agent.angle + sensorOffset), sin(agent.angle + sensorOffset));
    vec2 sensorCenter = agent.position + direction * sensorOffset;

    float weight = 0.0;
    for (uint i=-sensorSize; i <= sensorSize; i++) {
        for(uint j=-sensorSize; j<=sensorSize; j++) {
            vec2 sensorPos = sensorCenter + vec2(i, j);
            // if (sensorPos.x >= 0.0 && sensorPos.x < imageSize.x && sensorPos.y >= 0.0 && sensorPos.y < imageSize.y) {
            //     vec4 color = imageLoad(outputTexture, ivec2(sensorPos));
            //     weight += color.x;
            // }
            vec4 color = imageLoad(outputTexture, ivec2(sensorPos));
            weight += color.x;
        }
    }
    return weight;
}

void main() {
    uint index = gl_GlobalInvocationID.x;
    if (index >= ssboSize) {
        return;
    }

    Agent agent = ssbo.agents[index];
    vec2 pos = agent.position;
    vec2 imageSize = vec2(imageSize(outputTexture));

    float rand = random(time + index);

    float weightForward = sense(agent, 0.0, imageSize);
    float weightLeft = sense(agent, sensorAngleRad, imageSize);
    float weightRight = sense(agent, -sensorAngleRad, imageSize);

    //agent.angle -= turnSpeed;
    if (weightForward > weightLeft && weightForward > weightRight) {
        agent.angle += 0.0;
    }else if (weightRight > weightLeft) {
        agent.angle -= turnSpeed;
    }else if (weightLeft > weightRight) {
        agent.angle += turnSpeed;
    }

    vec2 direction = vec2(cos(agent.angle), sin(agent.angle));
    agent.position += direction;

    if (agent.position.x < 0.0 || agent.position.x >= imageSize.x || agent.position.y < 0.0 || agent.position.y >= imageSize.y) {
        agent.angle = rand * 2.0 * 3.1415;
        agent.position.x = min(imageSize.x - 1, max(0, agent.position.x));
        agent.position.y = min(imageSize.y - 1, max(0, agent.position.y));
    }

    ssbo.agents[index] = agent;

    imageStore(outputTexture, ivec2(agent.position), vec4(1.0, 1.0, 1.0, 1.0));
}