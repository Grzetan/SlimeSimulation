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
float sensorAngleRad = 20 * 0.0174533;
int sensorSize = 1;
uint sensorLength = 5;
float timeSpeed = 1;
float turnSpeed = 5 * 0.0174533 * timeSpeed;

layout (rgba32f, binding = 1) uniform image2D inputTexture;
layout (rgba32f, binding = 2) uniform image2D outputTexture;

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
    vec2 sensorCenter = agent.position + direction * sensorLength;

    float weight = 0.0;
    for (int i=-sensorSize; i <= sensorSize; i++) {
        for(int j=-sensorSize; j<=sensorSize; j++) {
            vec2 sensorPos = sensorCenter + vec2(i, j);
            vec4 color = imageLoad(inputTexture, ivec2(sensorPos));
            weight += color.r;
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

    if(weightForward > weightRight && weightForward > weightLeft) {
        agent.position += 0.0;
    }else if(weightForward < weightRight && weightForward < weightLeft) {
        if(rand > 0.5) {
            agent.angle -= turnSpeed;
        } else {
            agent.angle += turnSpeed;
        }
    }else if (weightRight > weightLeft) {
        agent.angle -= turnSpeed;
    }else if (weightLeft > weightRight) {
        agent.angle += turnSpeed;
    }

    vec2 direction = vec2(cos(agent.angle), sin(agent.angle));
    agent.position += direction * timeSpeed;

    if (agent.position.x < 0.0 || agent.position.x >= imageSize.x || agent.position.y < 0.0 || agent.position.y >= imageSize.y) {
        agent.angle = rand * 2.0 * 3.1415;
        agent.position.x = min(imageSize.x - 1, max(0, agent.position.x));
        agent.position.y = min(imageSize.y - 1, max(0, agent.position.y));
    }

    ssbo.agents[index] = agent;

    imageStore(outputTexture, ivec2(agent.position), vec4(1.0, 1.0, 1.0, 1.0));
}